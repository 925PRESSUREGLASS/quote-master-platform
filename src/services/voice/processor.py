"""Voice processing service for Quote Master Pro."""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json
import numpy as np
from datetime import datetime

from .recognizer import VoiceRecognizer
from .whisper import WhisperService
from src.services.ai.orchestrator import get_ai_orchestrator
from src.core.config import get_settings
from src.core.exceptions import VoiceProcessingException

logger = logging.getLogger(__name__)
settings = get_settings()


class VoiceProcessor:
    """Comprehensive voice processing service."""
    
    def __init__(self):
        self.recognizer = VoiceRecognizer()
        self.whisper_service = WhisperService()
        self.ai_orchestrator = get_ai_orchestrator()
        self._processing_queue = asyncio.Queue()
        self._is_processing = False
    
    async def process_audio_file(
        self,
        file_path: str,
        processing_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an audio file with various analysis options."""
        
        try:
            logger.info(f"Starting audio processing for {file_path}")
            
            # Initialize result structure
            result = {
                "file_path": file_path,
                "processing_started": datetime.utcnow().isoformat(),
                "success": False,
                "transcription": None,
                "analysis": {},
                "errors": []
            }
            
            # Step 1: Basic file validation
            if not Path(file_path).exists():
                raise VoiceProcessingException(f"Audio file not found: {file_path}")
            
            # Step 2: Audio quality analysis
            if processing_options.get("analyze_quality", True):
                logger.info("Analyzing audio quality...")
                quality_result = await self.recognizer.analyze_audio_quality(file_path)
                result["analysis"]["quality"] = quality_result
            
            # Step 3: Transcription
            transcription_engine = processing_options.get("transcription_engine", "whisper")
            
            if transcription_engine == "whisper":
                transcription_result = await self.whisper_service.transcribe_file(
                    file_path,
                    model=processing_options.get("whisper_model", "base"),
                    language=processing_options.get("language"),
                    task=processing_options.get("task", "transcribe")
                )
            else:
                transcription_result = await self.recognizer.transcribe_file(
                    file_path,
                    engine=transcription_engine,
                    language=processing_options.get("language", "en-US")
                )
            
            if transcription_result["success"]:
                result["transcription"] = transcription_result
                logger.info("Transcription completed successfully")
            else:
                result["errors"].append(f"Transcription failed: {transcription_result.get('error', 'Unknown error')}")
                logger.warning("Transcription failed")
            
            # Step 4: Language detection (if not specified)
            if not processing_options.get("language") and result["transcription"]:
                logger.info("Detecting language...")
                language_result = await self.recognizer.detect_language(file_path)
                result["analysis"]["language_detection"] = language_result
            
            # Step 5: Text analysis (if transcription succeeded)
            if result["transcription"] and processing_options.get("analyze_text", True):
                await self._analyze_transcribed_text(
                    result["transcription"]["transcription"],
                    result,
                    processing_options
                )
            
            # Step 6: Voice characteristics analysis
            if processing_options.get("analyze_voice", True):
                logger.info("Analyzing voice characteristics...")
                voice_analysis = await self._analyze_voice_characteristics(file_path)
                result["analysis"]["voice_characteristics"] = voice_analysis
            
            # Step 7: Generate insights and recommendations
            if processing_options.get("generate_insights", True):
                await self._generate_processing_insights(result, processing_options)
            
            result["success"] = True
            result["processing_completed"] = datetime.utcnow().isoformat()
            
            logger.info(f"Audio processing completed successfully for {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Audio processing failed for {file_path}: {str(e)}")
            result["success"] = False
            result["errors"].append(str(e))
            result["processing_completed"] = datetime.utcnow().isoformat()
            return result
    
    async def _analyze_transcribed_text(
        self,
        text: str,
        result: Dict[str, Any],
        options: Dict[str, Any]
    ) -> None:
        """Analyze the transcribed text using AI services."""
        
        try:
            # Sentiment analysis
            if options.get("analyze_sentiment", True):
                logger.info("Performing sentiment analysis...")
                sentiment_response = await self.ai_orchestrator.analyze_text(
                    text, 
                    analysis_type="sentiment"
                )
                
                if sentiment_response.success:
                    result["analysis"]["sentiment"] = {
                        "analysis": sentiment_response.content,
                        "confidence": sentiment_response.confidence_score,
                        "model_used": sentiment_response.model_used
                    }
            
            # Emotional analysis
            if options.get("analyze_emotion", True):
                logger.info("Performing emotional analysis...")
                emotion_response = await self.ai_orchestrator.analyze_text(
                    text,
                    analysis_type="psychology"
                )
                
                if emotion_response.success:
                    result["analysis"]["emotion"] = {
                        "analysis": emotion_response.content,
                        "confidence": emotion_response.confidence_score,
                        "model_used": emotion_response.model_used
                    }
            
            # Theme and content analysis
            if options.get("analyze_themes", True):
                logger.info("Performing theme analysis...")
                theme_response = await self.ai_orchestrator.analyze_text(
                    text,
                    analysis_type="themes"
                )
                
                if theme_response.success:
                    result["analysis"]["themes"] = {
                        "analysis": theme_response.content,
                        "confidence": theme_response.confidence_score,
                        "model_used": theme_response.model_used
                    }
            
            # Extract keywords and key phrases
            if options.get("extract_keywords", True):
                keywords = await self._extract_keywords(text)
                result["analysis"]["keywords"] = keywords
            
        except Exception as e:
            logger.error(f"Text analysis failed: {str(e)}")
            result["errors"].append(f"Text analysis error: {str(e)}")
    
    async def _analyze_voice_characteristics(self, file_path: str) -> Dict[str, Any]:
        """Analyze voice characteristics from audio file."""
        
        try:
            # This is a simplified implementation
            # In a production system, you'd use more sophisticated audio analysis
            
            import librosa
            
            # Load audio file
            y, sr = librosa.load(file_path)
            
            # Extract basic features
            features = {}
            
            # Tempo and rhythm
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            features["tempo"] = float(tempo)
            
            # Pitch analysis
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[pitches > 0]
            if len(pitch_values) > 0:
                features["average_pitch"] = float(np.mean(pitch_values))
                features["pitch_variance"] = float(np.var(pitch_values))
            
            # Energy and volume
            rms = librosa.feature.rms(y=y)[0]
            features["average_energy"] = float(np.mean(rms))
            features["energy_variance"] = float(np.var(rms))
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features["spectral_centroid"] = float(np.mean(spectral_centroids))
            
            # Duration
            features["duration"] = float(len(y) / sr)
            
            # Speaking rate estimation
            if features["duration"] > 0:
                # This is a rough estimate - would need more sophisticated analysis
                features["estimated_speaking_rate"] = len(y) / (sr * features["duration"])
            
            return {
                "features": features,
                "analysis_method": "librosa_basic",
                "confidence": 0.7
            }
            
        except ImportError:
            logger.warning("librosa not available, using basic analysis")
            return {
                "features": {},
                "analysis_method": "basic",
                "confidence": 0.3,
                "note": "Advanced audio analysis requires librosa package"
            }
        except Exception as e:
            logger.error(f"Voice characteristics analysis failed: {str(e)}")
            return {
                "features": {},
                "error": str(e),
                "confidence": 0.0
            }
    
    async def _extract_keywords(self, text: str) -> Dict[str, Any]:
        """Extract keywords and key phrases from text."""
        
        try:
            # Simple keyword extraction using frequency analysis
            import re
            from collections import Counter
            
            # Clean and tokenize text
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Remove common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
                'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
                'can', 'may', 'might', 'must', 'i', 'you', 'he', 'she', 'it', 'we',
                'they', 'this', 'that', 'these', 'those', 'here', 'there', 'where',
                'when', 'why', 'how', 'what', 'who', 'which'
            }
            
            # Filter words
            filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]
            
            # Count frequencies
            word_freq = Counter(filtered_words)
            
            # Get top keywords
            top_keywords = word_freq.most_common(10)
            
            return {
                "keywords": [{"word": word, "frequency": freq} for word, freq in top_keywords],
                "total_words": len(words),
                "unique_words": len(set(words)),
                "method": "frequency_analysis"
            }
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {str(e)}")
            return {
                "keywords": [],
                "error": str(e)
            }
    
    async def _generate_processing_insights(
        self,
        result: Dict[str, Any],
        options: Dict[str, Any]
    ) -> None:
        """Generate insights and recommendations from processing results."""
        
        try:
            insights = []
            recommendations = []
            
            # Quality insights
            if "quality" in result["analysis"]:
                quality = result["analysis"]["quality"]
                quality_score = quality.get("quality_score", 0.5)
                
                if quality_score > 0.8:
                    insights.append("Excellent audio quality detected")
                elif quality_score > 0.6:
                    insights.append("Good audio quality for processing")
                else:
                    insights.append("Audio quality could be improved")
                    recommendations.extend(quality.get("recommendations", []))
            
            # Transcription insights
            if result["transcription"] and result["transcription"]["success"]:
                confidence = result["transcription"].get("confidence", 0.0)
                
                if confidence > 0.9:
                    insights.append("High confidence transcription achieved")
                elif confidence > 0.7:
                    insights.append("Good transcription quality")
                else:
                    insights.append("Transcription confidence could be improved")
                    recommendations.append("Consider using higher quality audio or different transcription engine")
            
            # Content insights
            if "sentiment" in result["analysis"]:
                insights.append("Sentiment analysis completed")
            
            if "emotion" in result["analysis"]:
                insights.append("Emotional analysis provided psychological insights")
            
            if "themes" in result["analysis"]:
                insights.append("Theme analysis identified key topics")
            
            # Voice characteristics insights
            if "voice_characteristics" in result["analysis"]:
                voice_features = result["analysis"]["voice_characteristics"].get("features", {})
                
                if "duration" in voice_features:
                    duration = voice_features["duration"]
                    if duration < 5:
                        insights.append("Short audio clip - consider longer recordings for better analysis")
                    elif duration > 300:  # 5 minutes
                        insights.append("Long audio clip - processing may take additional time")
            
            result["analysis"]["insights"] = {
                "summary": insights,
                "recommendations": recommendations,
                "processing_quality": self._assess_processing_quality(result)
            }
            
        except Exception as e:
            logger.error(f"Insight generation failed: {str(e)}")
            result["errors"].append(f"Insight generation error: {str(e)}")
    
    def _assess_processing_quality(self, result: Dict[str, Any]) -> str:
        """Assess overall processing quality."""
        
        try:
            quality_factors = []
            
            # Transcription quality
            if result["transcription"] and result["transcription"]["success"]:
                confidence = result["transcription"].get("confidence", 0.0)
                quality_factors.append(confidence)
            
            # Audio quality
            if "quality" in result["analysis"]:
                audio_quality = result["analysis"]["quality"].get("quality_score", 0.5)
                quality_factors.append(audio_quality)
            
            # Analysis completeness
            analysis_count = len([k for k in result["analysis"].keys() if k not in ["insights"]])
            completeness_score = min(1.0, analysis_count / 5)  # Normalize to 0-1
            quality_factors.append(completeness_score)
            
            if quality_factors:
                overall_quality = np.mean(quality_factors)
                
                if overall_quality > 0.8:
                    return "excellent"
                elif overall_quality > 0.6:
                    return "good"
                elif overall_quality > 0.4:
                    return "fair"
                else:
                    return "poor"
            
            return "unknown"
            
        except Exception:
            return "unknown"
    
    async def convert_voice_to_quote(
        self,
        file_path: str,
        quote_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert voice recording to an inspirational quote."""
        
        try:
            logger.info(f"Converting voice to quote: {file_path}")
            
            # First, transcribe the audio
            transcription_result = await self.whisper_service.transcribe_file(file_path)
            
            if not transcription_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to transcribe audio",
                    "transcription_error": transcription_result.get("error")
                }
            
            transcribed_text = transcription_result["transcription"]
            
            # Analyze the transcribed text for context
            analysis_result = await self.ai_orchestrator.analyze_text(
                transcribed_text,
                analysis_type="comprehensive"
            )
            
            # Generate quote based on the transcribed content
            quote_prompt = self._build_quote_prompt(transcribed_text, quote_options, analysis_result)
            
            quote_response = await self.ai_orchestrator.generate_quote(
                prompt=quote_prompt,
                style=quote_options.get("style"),
                tone=quote_options.get("tone"),
                length=quote_options.get("length"),
                context=f"Based on voice recording: {transcribed_text[:200]}..."
            )
            
            if quote_response.success:
                return {
                    "success": True,
                    "quote": quote_response.content,
                    "original_transcription": transcribed_text,
                    "analysis": analysis_result.content if analysis_result.success else None,
                    "metadata": {
                        "model_used": quote_response.model_used,
                        "confidence": quote_response.confidence_score,
                        "processing_time": quote_response.processing_time
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate quote",
                    "ai_error": quote_response.error_message
                }
                
        except Exception as e:
            logger.error(f"Voice to quote conversion failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_quote_prompt(
        self,
        transcribed_text: str,
        quote_options: Dict[str, Any],
        analysis_result: Any
    ) -> str:
        """Build a prompt for quote generation based on voice input."""
        
        prompt_parts = [
            f"Based on this spoken content: '{transcribed_text}'"
        ]
        
        if analysis_result and analysis_result.success:
            prompt_parts.append(f"Analysis insights: {analysis_result.content[:300]}...")
        
        prompt_parts.extend([
            "Create an inspirational quote that:",
            "- Captures the essence and emotion of the spoken words",
            "- Transforms the personal expression into universal wisdom",
            "- Maintains the authentic voice and sentiment",
            "- Creates something memorable and shareable"
        ])
        
        if quote_options.get("preserve_personal_elements"):
            prompt_parts.append("- Preserves personal elements and individual perspective")
        
        return "\n".join(prompt_parts)
    
    async def start_processing_queue(self) -> None:
        """Start the background processing queue."""
        if not self._is_processing:
            self._is_processing = True
            asyncio.create_task(self._process_queue())
            logger.info("Voice processing queue started")
    
    async def stop_processing_queue(self) -> None:
        """Stop the background processing queue."""
        self._is_processing = False
        logger.info("Voice processing queue stopped")
    
    async def add_to_queue(self, processing_task: Dict[str, Any]) -> None:
        """Add a processing task to the queue."""
        await self._processing_queue.put(processing_task)
        logger.info(f"Added processing task to queue: {processing_task.get('task_id')}")
    
    async def _process_queue(self) -> None:
        """Process items in the background queue."""
        while self._is_processing:
            try:
                # Wait for a task with timeout
                task = await asyncio.wait_for(
                    self._processing_queue.get(),
                    timeout=1.0
                )
                
                # Process the task
                await self._process_queued_task(task)
                
            except asyncio.TimeoutError:
                # Continue processing loop
                continue
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}")
    
    async def _process_queued_task(self, task: Dict[str, Any]) -> None:
        """Process a single queued task."""
        
        try:
            task_type = task.get("type")
            
            if task_type == "process_audio":
                result = await self.process_audio_file(
                    task["file_path"],
                    task["options"]
                )
            elif task_type == "voice_to_quote":
                result = await self.convert_voice_to_quote(
                    task["file_path"],
                    task["options"]
                )
            else:
                logger.warning(f"Unknown task type: {task_type}")
                return
            
            # Store or callback with result
            if "callback" in task:
                await task["callback"](result)
            
            logger.info(f"Completed queued task: {task.get('task_id')}")
            
        except Exception as e:
            logger.error(f"Queued task processing failed: {str(e)}")


# Global processor instance
_processor = None


def get_voice_processor() -> VoiceProcessor:
    """Get the global voice processor instance."""
    global _processor
    if _processor is None:
        _processor = VoiceProcessor()
    return _processor