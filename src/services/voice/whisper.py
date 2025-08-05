"""OpenAI Whisper service implementation for Quote Master Pro."""

import whisper
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import os

from src.core.config import get_settings
from src.core.exceptions import VoiceProcessingException, WhisperException

logger = logging.getLogger(__name__)
settings = get_settings()


class WhisperService:
    """OpenAI Whisper service for high-quality speech recognition."""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.whisper_model
        self.model = None
        self.model_cache = {}
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize Whisper model."""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info(f"Whisper model {self.model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise WhisperException(f"Failed to initialize Whisper: {str(e)}")
    
    async def transcribe_file(
        self,
        file_path: str,
        model: Optional[str] = None,
        language: Optional[str] = None,
        task: str = "transcribe",
        temperature: float = 0.0,
        word_timestamps: bool = False,
        initial_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio file using Whisper."""
        
        try:
            # Validate file exists
            if not Path(file_path).exists():
                raise WhisperException(f"Audio file not found: {file_path}")
            
            # Use different model if specified
            whisper_model = self.model
            if model and model != self.model_name:
                whisper_model = await self._get_or_load_model(model)
            
            # Prepare transcription options
            options = {
                "language": language,
                "task": task,  # "transcribe" or "translate"
                "temperature": temperature,
                "word_timestamps": word_timestamps,
                "initial_prompt": initial_prompt,
                "fp16": False  # Use fp32 for better compatibility
            }
            
            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}
            
            # Run transcription in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: whisper_model.transcribe(file_path, **options)
            )
            
            # Process and format results
            return self._format_whisper_result(result, file_path, options)
            
        except Exception as e:
            logger.error(f"Whisper transcription failed for {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "transcription_failed",
                "transcription": "",
                "confidence": 0.0,
                "file_path": file_path
            }
    
    def _format_whisper_result(
        self,
        result: Dict[str, Any],
        file_path: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format Whisper result into standardized format."""
        
        try:
            # Extract main transcription text
            transcription_text = result.get("text", "").strip()
            
            # Calculate average confidence from segments
            segments = result.get("segments", [])
            if segments:
                # Whisper doesn't provide confidence scores in the same way
                # We'll estimate confidence based on segment characteristics
                confidence = self._estimate_confidence(segments)
            else:
                confidence = 0.8  # Default confidence for successful transcription
            
            # Detect language if not specified
            detected_language = result.get("language", "unknown")
            
            # Format segments with timestamps
            formatted_segments = []
            for segment in segments:
                formatted_segment = {
                    "start": segment.get("start", 0.0),
                    "end": segment.get("end", 0.0),
                    "text": segment.get("text", "").strip(),
                    "words": segment.get("words", []) if options.get("word_timestamps") else []
                }
                formatted_segments.append(formatted_segment)
            
            return {
                "success": True,
                "transcription": transcription_text,
                "confidence": confidence,
                "language": detected_language,
                "segments": formatted_segments,
                "word_count": len(transcription_text.split()) if transcription_text else 0,
                "duration": self._calculate_duration(segments),
                "model_used": self.model_name,
                "task": options.get("task", "transcribe"),
                "file_path": file_path,
                "metadata": {
                    "raw_result": result,
                    "processing_options": options
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to format Whisper result: {str(e)}")
            return {
                "success": False,
                "error": f"Result formatting failed: {str(e)}",
                "transcription": "",
                "confidence": 0.0
            }
    
    def _estimate_confidence(self, segments: List[Dict[str, Any]]) -> float:
        """Estimate confidence score from Whisper segments."""
        
        if not segments:
            return 0.5
        
        # Factors that indicate higher confidence:
        # - Longer segments (more context)
        # - Consistent segment lengths
        # - Presence of punctuation
        # - Reasonable speaking pace
        
        confidence_factors = []
        
        for segment in segments:
            text = segment.get("text", "").strip()
            start = segment.get("start", 0.0)
            end = segment.get("end", 0.0)
            duration = end - start
            
            # Text length factor
            text_length = len(text)
            if text_length > 50:
                length_factor = 0.9
            elif text_length > 20:
                length_factor = 0.8
            elif text_length > 5:
                length_factor = 0.7
            else:
                length_factor = 0.5
            
            # Speaking rate factor
            if duration > 0:
                speaking_rate = len(text.split()) / duration
                if 1.5 <= speaking_rate <= 4.0:  # Normal speaking rate
                    rate_factor = 0.9
                elif 1.0 <= speaking_rate <= 5.0:
                    rate_factor = 0.8
                else:
                    rate_factor = 0.6
            else:
                rate_factor = 0.5
            
            # Punctuation factor (indicates proper sentence structure)
            punctuation_count = sum(1 for char in text if char in '.,!?;:')
            punct_factor = min(0.9, 0.6 + (punctuation_count * 0.1))
            
            # Combine factors
            segment_confidence = (length_factor + rate_factor + punct_factor) / 3
            confidence_factors.append(segment_confidence)
        
        # Return average confidence, weighted by segment length
        if confidence_factors:
            return min(0.95, max(0.1, sum(confidence_factors) / len(confidence_factors)))
        
        return 0.5
    
    def _calculate_duration(self, segments: List[Dict[str, Any]]) -> float:
        """Calculate total duration from segments."""
        
        if not segments:
            return 0.0
        
        last_segment = max(segments, key=lambda s: s.get("end", 0.0))
        return last_segment.get("end", 0.0)
    
    async def _get_or_load_model(self, model_name: str) -> Any:
        """Get or load a Whisper model from cache."""
        
        if model_name in self.model_cache:
            return self.model_cache[model_name]
        
        try:
            logger.info(f"Loading additional Whisper model: {model_name}")
            
            # Load model in executor
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                None,
                lambda: whisper.load_model(model_name)
            )
            
            # Cache the model
            self.model_cache[model_name] = model
            logger.info(f"Whisper model {model_name} loaded and cached")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model {model_name}: {str(e)}")
            raise WhisperException(f"Failed to load model {model_name}: {str(e)}")
    
    async def transcribe_with_translation(
        self,
        file_path: str,
        target_language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """Transcribe and translate audio to target language."""
        
        # First transcribe in original language
        transcription_result = await self.transcribe_file(
            file_path,
            task="transcribe",
            **kwargs
        )
        
        if not transcription_result["success"]:
            return transcription_result
        
        # Then translate to target language
        translation_result = await self.transcribe_file(
            file_path,
            task="translate",
            language=target_language,
            **kwargs
        )
        
        # Combine results
        return {
            "success": True,
            "original_transcription": transcription_result,
            "translation": translation_result,
            "target_language": target_language
        }
    
    async def batch_transcribe(
        self,
        file_paths: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Transcribe multiple audio files."""
        
        # Create transcription tasks
        tasks = [
            self.transcribe_file(file_path, **kwargs)
            for file_path in file_paths
        ]
        
        # Run tasks concurrently (but limit concurrency to avoid memory issues)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent transcriptions
        
        async def transcribe_with_semaphore(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(
            *[transcribe_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "file_path": file_paths[i],
                    "transcription": "",
                    "confidence": 0.0
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models."""
        return [
            "tiny",      # 39 MB, ~32x realtime
            "base",      # 74 MB, ~16x realtime  
            "small",     # 244 MB, ~6x realtime
            "medium",    # 769 MB, ~2x realtime
            "large",     # 1550 MB, ~1x realtime
            "large-v2",  # 1550 MB, improved version
            "large-v3"   # 1550 MB, latest version
        ]
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a Whisper model."""
        
        model_info = {
            "tiny": {
                "size": "39 MB",
                "speed": "~32x realtime",
                "accuracy": "lowest",
                "languages": 99,
                "use_case": "Fast processing, lower accuracy"
            },
            "base": {
                "size": "74 MB", 
                "speed": "~16x realtime",
                "accuracy": "low",
                "languages": 99,
                "use_case": "Balanced speed and accuracy"
            },
            "small": {
                "size": "244 MB",
                "speed": "~6x realtime", 
                "accuracy": "medium",
                "languages": 99,
                "use_case": "Good accuracy with reasonable speed"
            },
            "medium": {
                "size": "769 MB",
                "speed": "~2x realtime",
                "accuracy": "high", 
                "languages": 99,
                "use_case": "High accuracy applications"
            },
            "large": {
                "size": "1550 MB",
                "speed": "~1x realtime",
                "accuracy": "highest",
                "languages": 99,
                "use_case": "Maximum accuracy, slower processing"
            },
            "large-v2": {
                "size": "1550 MB",
                "speed": "~1x realtime", 
                "accuracy": "highest",
                "languages": 99,
                "use_case": "Improved large model"
            },
            "large-v3": {
                "size": "1550 MB",
                "speed": "~1x realtime",
                "accuracy": "highest", 
                "languages": 99,
                "use_case": "Latest and most accurate model"
            }
        }
        
        return model_info.get(model_name, {
            "error": f"Unknown model: {model_name}",
            "available_models": list(model_info.keys())
        })
    
    async def analyze_audio_language(self, file_path: str) -> Dict[str, Any]:
        """Analyze the language of audio file using Whisper."""
        
        try:
            # Load audio and detect language
            loop = asyncio.get_event_loop()
            
            # Use Whisper's detect_language function
            audio = await loop.run_in_executor(
                None,
                lambda: whisper.load_audio(file_path)
            )
            
            # Detect language
            language_result = await loop.run_in_executor(
                None,
                lambda: whisper.detect_language(self.model, audio)
            )
            
            language_code, confidence = language_result
            
            return {
                "detected_language": language_code,
                "confidence": confidence,
                "model_used": self.model_name,
                "method": "whisper_detection"
            }
            
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return {
                "detected_language": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def get_supported_languages(self) -> List[str]:
        """Get list of languages supported by Whisper."""
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca", "nl",
            "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms", "cs", "ro",
            "da", "hu", "ta", "no", "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy",
            "sk", "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk", "br", "eu",
            "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km",
            "sn", "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi", "lo",
            "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl", "mg",
            "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]