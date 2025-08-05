"""Voice recognition service for Quote Master Pro."""

import speech_recognition as sr
from typing import Dict, Any, Optional, List, Tuple
import logging
import asyncio
import io
import wave
from pathlib import Path

from src.core.config import get_settings
from src.core.exceptions import VoiceProcessingException

logger = logging.getLogger(__name__)
settings = get_settings()


class VoiceRecognizer:
    """Voice recognition service using multiple engines."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self._initialize_settings()
    
    def _initialize_settings(self) -> None:
        """Initialize recognition settings."""
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.8
        self.recognizer.operation_timeout = None
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5
    
    async def transcribe_file(
        self,
        file_path: str,
        engine: str = "google",
        language: str = "en-US",
        show_all: bool = False
    ) -> Dict[str, Any]:
        """Transcribe audio file to text."""
        
        try:
            # Load audio file
            with sr.AudioFile(file_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                # Record the audio
                audio = self.recognizer.record(source)
            
            # Transcribe using selected engine
            result = await self._transcribe_audio(audio, engine, language, show_all)
            
            return {
                "success": True,
                "transcription": result["text"],
                "confidence": result.get("confidence", 1.0),
                "engine": engine,
                "language": language,
                "alternatives": result.get("alternatives", []),
                "metadata": {
                    "file_path": file_path,
                    "audio_duration": self._get_audio_duration(file_path),
                    "engine_specific": result.get("raw_data", {})
                }
            }
            
        except sr.UnknownValueError:
            return {
                "success": False,
                "error": "Could not understand audio",
                "error_type": "recognition_failed",
                "transcription": "",
                "confidence": 0.0
            }
        except sr.RequestError as e:
            return {
                "success": False,
                "error": f"Recognition service error: {str(e)}",
                "error_type": "service_error",
                "transcription": "",
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"Voice recognition error: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unknown_error",
                "transcription": "",
                "confidence": 0.0
            }
    
    async def _transcribe_audio(
        self,
        audio: sr.AudioData,
        engine: str,
        language: str,
        show_all: bool
    ) -> Dict[str, Any]:
        """Transcribe audio using specified engine."""
        
        loop = asyncio.get_event_loop()
        
        if engine == "google":
            result = await loop.run_in_executor(
                None,
                lambda: self.recognizer.recognize_google(
                    audio, language=language, show_all=show_all
                )
            )
        elif engine == "google_cloud":
            result = await loop.run_in_executor(
                None,
                lambda: self.recognizer.recognize_google_cloud(
                    audio, language=language, show_all=show_all
                )
            )
        elif engine == "sphinx":
            result = await loop.run_in_executor(
                None,
                lambda: self.recognizer.recognize_sphinx(audio, language=language)
            )
        elif engine == "wit":
            # Note: Requires Wit.ai API key
            result = await loop.run_in_executor(
                None,
                lambda: self.recognizer.recognize_wit(audio, show_all=show_all)
            )
        elif engine == "azure":
            # Note: Requires Azure Speech API key
            result = await loop.run_in_executor(
                None,
                lambda: self.recognizer.recognize_azure(
                    audio, language=language, show_all=show_all
                )
            )
        else:
            raise ValueError(f"Unsupported recognition engine: {engine}")
        
        # Normalize result format
        if isinstance(result, str):
            return {
                "text": result,
                "confidence": 1.0,
                "alternatives": []
            }
        elif isinstance(result, dict):
            if show_all:
                # Handle detailed results
                alternatives = result.get("alternative", [])
                if alternatives:
                    best_result = alternatives[0]
                    return {
                        "text": best_result.get("transcript", ""),
                        "confidence": best_result.get("confidence", 1.0),
                        "alternatives": [
                            {
                                "text": alt.get("transcript", ""),
                                "confidence": alt.get("confidence", 1.0)
                            }
                            for alt in alternatives[1:]
                        ],
                        "raw_data": result
                    }
            return {
                "text": str(result),
                "confidence": 1.0,
                "alternatives": []
            }
        else:
            return {
                "text": str(result),
                "confidence": 1.0,
                "alternatives": []
            }
    
    def _get_audio_duration(self, file_path: str) -> float:
        """Get audio file duration in seconds."""
        try:
            with wave.open(file_path, 'rb') as audio_file:
                frames = audio_file.getnframes()
                sample_rate = audio_file.getframerate()
                duration = frames / float(sample_rate)
                return duration
        except Exception:
            return 0.0
    
    async def recognize_from_microphone(
        self,
        duration: Optional[float] = None,
        timeout: float = 1.0,
        engine: str = "google",
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """Recognize speech from microphone input."""
        
        try:
            if self.microphone is None:
                self.microphone = sr.Microphone()
            
            with self.microphone as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info("Listening for speech...")
                if duration:
                    audio = self.recognizer.record(source, duration=duration)
                else:
                    audio = self.recognizer.listen(source, timeout=timeout)
            
            logger.info("Processing speech...")
            result = await self._transcribe_audio(audio, engine, language, show_all=True)
            
            return {
                "success": True,
                "transcription": result["text"],
                "confidence": result.get("confidence", 1.0),
                "engine": engine,
                "language": language,
                "alternatives": result.get("alternatives", [])
            }
            
        except sr.WaitTimeoutError:
            return {
                "success": False,
                "error": "No speech detected within timeout period",
                "error_type": "timeout",
                "transcription": "",
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"Microphone recognition error: {str(e)}")
            return {
                "success": False,
                "error": f"Microphone error: {str(e)}",
                "error_type": "microphone_error",
                "transcription": "",
                "confidence": 0.0
            }
    
    async def batch_transcribe(
        self,
        file_paths: List[str],
        engine: str = "google",
        language: str = "en-US"
    ) -> List[Dict[str, Any]]:
        """Transcribe multiple audio files."""
        
        tasks = [
            self.transcribe_file(file_path, engine, language)
            for file_path in file_paths
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "error_type": "exception",
                    "file_path": file_paths[i],
                    "transcription": "",
                    "confidence": 0.0
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_supported_engines(self) -> List[str]:
        """Get list of supported recognition engines."""
        return ["google", "google_cloud", "sphinx", "wit", "azure"]
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            "en-US", "en-GB", "en-AU", "en-CA", "en-IN",
            "es-ES", "es-MX", "fr-FR", "de-DE", "it-IT",
            "pt-BR", "ru-RU", "ja-JP", "ko-KR", "zh-CN",
            "ar-SA", "hi-IN", "tr-TR", "pl-PL", "nl-NL"
        ]
    
    async def analyze_audio_quality(self, file_path: str) -> Dict[str, Any]:
        """Analyze audio quality for transcription suitability."""
        
        try:
            with sr.AudioFile(file_path) as source:
                # Sample first 5 seconds for analysis
                audio = self.recognizer.record(source, duration=5)
            
            # Convert to numpy array for analysis
            import numpy as np
            
            # Get raw audio data
            raw_data = audio.get_raw_data()
            audio_array = np.frombuffer(raw_data, dtype=np.int16)
            
            # Calculate audio metrics
            rms = np.sqrt(np.mean(audio_array**2))
            max_amplitude = np.max(np.abs(audio_array))
            snr_estimate = 20 * np.log10(rms) if rms > 0 else -60
            
            # Determine quality score
            if snr_estimate > -20:
                quality = "excellent"
                score = 0.9
            elif snr_estimate > -30:
                quality = "good"
                score = 0.7
            elif snr_estimate > -40:
                quality = "fair"
                score = 0.5
            else:
                quality = "poor"
                score = 0.3
            
            return {
                "quality_score": score,
                "quality_rating": quality,
                "signal_level": float(snr_estimate),
                "max_amplitude": int(max_amplitude),
                "rms_level": float(rms),
                "recommendations": self._get_quality_recommendations(score)
            }
            
        except Exception as e:
            logger.error(f"Audio quality analysis failed: {str(e)}")
            return {
                "quality_score": 0.5,
                "quality_rating": "unknown",
                "error": str(e)
            }
    
    def _get_quality_recommendations(self, score: float) -> List[str]:
        """Get recommendations based on audio quality score."""
        
        recommendations = []
        
        if score < 0.4:
            recommendations.extend([
                "Consider re-recording in a quieter environment",
                "Check microphone positioning and quality",
                "Reduce background noise if possible"
            ])
        elif score < 0.7:
            recommendations.extend([
                "Audio quality is acceptable but could be improved",
                "Consider using noise reduction if available"
            ])
        else:
            recommendations.append("Audio quality is good for transcription")
        
        return recommendations
    
    async def detect_language(self, file_path: str) -> Dict[str, Any]:
        """Detect the language of speech in audio file."""
        
        try:
            # Try transcribing with different languages and compare confidence
            languages_to_try = ["en-US", "es-ES", "fr-FR", "de-DE", "it-IT"]
            results = []
            
            for language in languages_to_try:
                try:
                    result = await self.transcribe_file(
                        file_path, 
                        engine="google", 
                        language=language
                    )
                    if result["success"]:
                        results.append({
                            "language": language,
                            "confidence": result["confidence"],
                            "text_length": len(result["transcription"])
                        })
                except Exception:
                    continue
            
            if results:
                # Sort by confidence and text length
                best_result = max(
                    results, 
                    key=lambda x: x["confidence"] * x["text_length"]
                )
                
                return {
                    "detected_language": best_result["language"],
                    "confidence": best_result["confidence"],
                    "all_results": results
                }
            else:
                return {
                    "detected_language": "unknown",
                    "confidence": 0.0,
                    "error": "Could not detect language"
                }
                
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return {
                "detected_language": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }