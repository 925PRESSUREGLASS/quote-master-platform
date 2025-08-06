"""
Voice Recording model for Quote Master Pro
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any

from src.config.database import Base

class VoiceRecording(Base):
    __tablename__ = "voice_recordings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File Information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # bytes
    duration = Column(Float)  # seconds
    
    # Audio Processing
    transcription = Column(Text)
    language_detected = Column(String(10))
    confidence_score = Column(Float)
    
    # AI Analysis
    emotion_analysis = Column(Text)  # JSON stored as text
    sentiment_score = Column(Float)  # -1 to 1
    key_phrases = Column(Text)  # JSON array stored as text
    
    # Processing Status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="voice_recordings")
    quotes = relationship("Quote", back_populates="voice_recording")

    def __repr__(self):
        return f"<VoiceRecording(id={self.id}, filename='{self.filename}', user_id={self.user_id})>"

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string"""
        if not self.duration:
            return "0:00"
        
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes}:{seconds:02d}"

    @property
    def file_size_formatted(self) -> str:
        """Get formatted file size string"""
        if not self.file_size:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

    def to_dict(self) -> Dict[str, Any]:
        """Convert voice recording to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_size_formatted": self.file_size_formatted,
            "duration": self.duration,
            "duration_formatted": self.duration_formatted,
            "transcription": self.transcription,
            "language_detected": self.language_detected,
            "confidence_score": self.confidence_score,
            "emotion_analysis": self.emotion_analysis,
            "sentiment_score": self.sentiment_score,
            "key_phrases": self.key_phrases,
            "is_processed": self.is_processed,
            "processing_error": self.processing_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert voice recording to summary dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "duration_formatted": self.duration_formatted,
            "file_size_formatted": self.file_size_formatted,
            "is_processed": self.is_processed,
            "sentiment_score": self.sentiment_score,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }