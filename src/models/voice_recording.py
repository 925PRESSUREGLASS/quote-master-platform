"""
Voice Recording model for Quote Master Pro
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum as PyEnum

from src.config.database import Base

class AudioFormat(PyEnum):
    """Supported audio file formats"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    WEBM = "webm"
    M4A = "m4a"
    FLAC = "flac"

class VoiceRecordingStatus(PyEnum):
    """Status of voice recording processing"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"

class VoiceRecording(Base):
    __tablename__ = "voice_recordings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)  # User's original filename
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # bytes
    file_format = Column(Enum(AudioFormat), nullable=True)
    duration_seconds = Column(Float)  # seconds
    
    # Audio Processing
    transcription = Column(Text)
    language_detected = Column(String(10))  # ISO language code
    confidence_score = Column(Float)  # 0 to 1 transcription confidence
    
    # AI Analysis
    emotion_analysis = Column(Text)  # JSON stored as text
    sentiment_score = Column(Float)  # -1 to 1 (negative to positive)
    key_phrases = Column(Text)  # JSON array stored as text
    topics_detected = Column(Text)  # JSON array of detected topics
    
    # Processing Status
    status = Column(Enum(VoiceRecordingStatus), default=VoiceRecordingStatus.UPLOADED)
    processing_error = Column(Text)
    processing_attempts = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    transcribed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="voice_recordings")
    quotes = relationship("Quote", back_populates="voice_recording")  # Legacy
    service_quotes = relationship("ServiceQuote", back_populates="voice_recording")

    def __repr__(self):
        return f"<VoiceRecording(id={self.id}, filename='{self.filename}')>"

    def is_processed(self):
        """Check if recording is fully processed"""
        try:
            # Use getattr to get the actual instance value
            status = getattr(self, 'status', None)
            return status == VoiceRecordingStatus.PROCESSED
        except:
            return False

    def is_failed(self):
        """Check if processing failed"""
        try:
            status = getattr(self, 'status', None)
            return status == VoiceRecordingStatus.FAILED
        except:
            return False

    def duration_minutes(self):
        """Get duration in minutes"""
        try:
            duration = getattr(self, 'duration_seconds', None)
            return duration / 60 if duration else None
        except:
            return None

    def file_size_mb(self):
        """Get file size in MB"""
        try:
            size = getattr(self, 'file_size', None)
            return size / 1024 / 1024 if size else None
        except:
            return None

    def duration_formatted(self):
        """Get formatted duration string"""
        try:
            duration = getattr(self, 'duration_seconds', None)
            if not duration:
                return "0:00"
            
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}:{seconds:02d}"
        except:
            return "0:00"

    def file_size_formatted(self):
        """Get formatted file size string"""
        try:
            size = getattr(self, 'file_size', None)
            if not size:
                return "0 B"
            
            size_float = float(size)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_float < 1024.0:
                    return f"{size_float:.1f} {unit}"
                size_float /= 1024.0
            return f"{size_float:.1f} TB"
        except:
            return "0 B"

    def _safe_isoformat(self, attr_name):
        """Safely get isoformat from datetime attribute"""
        try:
            dt = getattr(self, attr_name, None)
            return dt.isoformat() if dt is not None else None
        except:
            return None

    def _safe_enum_value(self, attr_name, default=None):
        """Safely get value from enum attribute"""
        try:
            enum_val = getattr(self, attr_name, None)
            return enum_val.value if enum_val is not None else default
        except:
            return default

    def to_dict(self):
        """Convert to dictionary for API responses"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "user_id": getattr(self, 'user_id', None),
                "filename": getattr(self, 'filename', None),
                "original_filename": getattr(self, 'original_filename', None),
                "file_size": getattr(self, 'file_size', None),
                "file_format": self._safe_enum_value('file_format'),
                "duration_seconds": getattr(self, 'duration_seconds', None),
                "duration_formatted": self.duration_formatted(),
                "file_size_formatted": self.file_size_formatted(),
                "transcription": getattr(self, 'transcription', None),
                "language_detected": getattr(self, 'language_detected', None),
                "confidence_score": getattr(self, 'confidence_score', None),
                "emotion_analysis": getattr(self, 'emotion_analysis', None),
                "sentiment_score": getattr(self, 'sentiment_score', None),
                "key_phrases": getattr(self, 'key_phrases', None),
                "topics_detected": getattr(self, 'topics_detected', None),
                "status": self._safe_enum_value('status'),
                "processing_error": getattr(self, 'processing_error', None),
                "processing_attempts": getattr(self, 'processing_attempts', None),
                "created_at": self._safe_isoformat('created_at'),
                "updated_at": self._safe_isoformat('updated_at'),
                "processed_at": self._safe_isoformat('processed_at'),
                "transcribed_at": self._safe_isoformat('transcribed_at'),
                "is_processed": self.is_processed(),
                "duration_minutes": self.duration_minutes(),
                "file_size_mb": self.file_size_mb()
            }
        except Exception as e:
            # Return minimal data on error
            return {
                "id": getattr(self, 'id', None),
                "filename": getattr(self, 'filename', None),
                "status": "unknown",
                "error": str(e)
            }

    def to_summary_dict(self):
        """Convert voice recording to summary dictionary for lists"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "filename": getattr(self, 'filename', None),
                "original_filename": getattr(self, 'original_filename', None),
                "duration_formatted": self.duration_formatted(),
                "file_size_formatted": self.file_size_formatted(),
                "status": self._safe_enum_value('status', 'unknown'),
                "sentiment_score": getattr(self, 'sentiment_score', None),
                "language_detected": getattr(self, 'language_detected', None),
                "created_at": self._safe_isoformat('created_at'),
                "is_processed": self.is_processed()
            }
        except:
            return {
                "id": getattr(self, 'id', None),
                "filename": getattr(self, 'filename', 'unknown'),
                "status": "unknown"
            }