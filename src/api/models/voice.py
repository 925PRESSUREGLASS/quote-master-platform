"""Voice processing model definitions."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base
from src.core.database_types import GUID, new_uuid


class VoiceRecordingStatus(str, Enum):
    """Voice recording status enumeration."""

    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class VoiceProcessingStatus(str, Enum):
    """Voice processing job status enumeration."""

    PENDING = "pending"
    STARTED = "started"
    TRANSCRIBING = "transcribing"
    TRANSCRIBED = "transcribed"
    ANALYZING = "analyzing"
    GENERATING_QUOTE = "generating_quote"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AudioFormat(str, Enum):
    """Supported audio formats."""

    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    M4A = "m4a"
    FLAC = "flac"
    WEBM = "webm"


class VoiceRecording(Base):
    """Voice recording model."""

    __tablename__ = "voice_recordings"

    # Primary key
    id = Column(GUID(), primary_key=True, default=new_uuid)

    # Foreign key
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_format = Column(String(10), nullable=False)
    mime_type = Column(String(100), nullable=False)

    # Audio properties
    duration_seconds = Column(Float, nullable=True)
    sample_rate = Column(Integer, nullable=True)  # Hz
    bit_rate = Column(Integer, nullable=True)  # bps
    channels = Column(Integer, nullable=True)  # mono=1, stereo=2

    # Recording metadata
    recorded_at = Column(DateTime(timezone=True), nullable=True)
    device_info = Column(JSON, nullable=True)  # Recording device information
    quality_score = Column(Float, nullable=True)  # 0-1 audio quality assessment

    # Processing status
    status = Column(String(20), default=VoiceRecordingStatus.UPLOADED)

    # Transcription results
    transcription = Column(Text, nullable=True)
    transcription_confidence = Column(Float, nullable=True)  # 0-1
    language_detected = Column(String(10), nullable=True)  # ISO language code
    speaker_count = Column(Integer, nullable=True)  # Number of speakers detected

    # Analysis results
    emotional_analysis = Column(JSON, nullable=True)  # Emotional tone analysis
    content_categories = Column(JSON, nullable=True)  # Content categorization
    keywords = Column(JSON, nullable=True)  # Extracted keywords
    sentiment_score = Column(Float, nullable=True)  # -1 to 1

    # Processing metadata
    ai_model_used = Column(String(50), nullable=True)  # Which AI model processed it
    processing_duration = Column(Float, nullable=True)  # Processing time in seconds
    processing_cost = Column(Float, nullable=True)  # Cost in credits/dollars

    # Privacy and storage
    is_public = Column(Boolean, default=False)
    retain_audio = Column(Boolean, default=True)  # Whether to keep the audio file
    auto_delete_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="voice_recordings")
    processing_jobs = relationship(
        "VoiceProcessingJob", back_populates="recording", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<VoiceRecording(id={self.id}, filename={self.filename}, status={self.status})>"

    @property
    def is_processed(self) -> bool:
        """Check if recording has been processed."""
        return self.status == VoiceRecordingStatus.PROCESSED

    @property
    def has_transcription(self) -> bool:
        """Check if recording has transcription."""
        return bool(self.transcription and self.transcription.strip())

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024) if self.file_size else 0.0

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if not self.duration_seconds:
            return "00:00"

        minutes = int(self.duration_seconds // 60)
        seconds = int(self.duration_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"


class VoiceProcessingJob(Base):
    """Voice processing job tracking."""

    __tablename__ = "voice_processing_jobs"

    # Primary key
    id = Column(GUID(), primary_key=True, default=new_uuid)

    # Foreign keys
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    recording_id = Column(GUID(), ForeignKey("voice_recordings.id"), nullable=False)

    # Job information
    job_type = Column(
        String(50), nullable=False
    )  # transcription, analysis, quote_generation
    status = Column(String(20), default=VoiceProcessingStatus.PENDING)
    priority = Column(Integer, default=5)  # 1-10, higher = more priority

    # Processing parameters
    parameters = Column(JSON, nullable=True)  # Job-specific parameters
    model_config = Column(JSON, nullable=True)  # AI model configuration

    # Progress tracking
    progress_percent = Column(Float, default=0.0)  # 0-100
    current_step = Column(String(100), nullable=True)
    steps_total = Column(Integer, nullable=True)
    steps_completed = Column(Integer, default=0)

    # Results
    result_data = Column(JSON, nullable=True)  # Job results
    output_files = Column(JSON, nullable=True)  # Generated files

    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Performance metrics
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time = Column(Float, nullable=True)  # seconds
    cpu_time = Column(Float, nullable=True)  # CPU seconds used
    memory_peak = Column(Integer, nullable=True)  # Peak memory usage in MB

    # Cost tracking
    credits_used = Column(Float, nullable=True)
    cost_usd = Column(Float, nullable=True)

    # Worker information
    worker_id = Column(String(100), nullable=True)
    worker_version = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    recording = relationship("VoiceRecording", back_populates="processing_jobs")

    def __repr__(self) -> str:
        return f"<VoiceProcessingJob(id={self.id}, type={self.job_type}, status={self.status})>"

    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status == VoiceProcessingStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if job has failed."""
        return self.status == VoiceProcessingStatus.FAILED

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.is_failed and self.retry_count < self.max_retries

    def calculate_processing_time(self) -> Optional[float]:
        """Calculate processing time in seconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None

    def mark_started(self) -> None:
        """Mark job as started."""
        self.status = VoiceProcessingStatus.STARTED
        self.started_at = datetime.utcnow()

    def mark_completed(self, result_data: dict = None) -> None:
        """Mark job as completed."""
        self.status = VoiceProcessingStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100.0
        self.processing_time = self.calculate_processing_time()

        if result_data:
            self.result_data = result_data

    def mark_failed(self, error_message: str, error_code: str = None) -> None:
        """Mark job as failed."""
        self.status = VoiceProcessingStatus.FAILED
        self.error_message = error_message
        self.error_code = error_code
        self.completed_at = datetime.utcnow()
        self.processing_time = self.calculate_processing_time()

    def update_progress(self, percent: float, step: str = None) -> None:
        """Update job progress."""
        self.progress_percent = min(100.0, max(0.0, percent))
        if step:
            self.current_step = step
        self.updated_at = datetime.utcnow()


class VoiceModel(Base):
    """Voice AI model configuration."""

    __tablename__ = "voice_models"

    # Primary key
    id = Column(GUID(), primary_key=True, default=new_uuid)

    # Model information
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)

    # Model type and capabilities
    model_type = Column(
        String(50), nullable=False
    )  # transcription, analysis, generation
    provider = Column(String(50), nullable=False)  # openai, anthropic, custom
    capabilities = Column(JSON, nullable=True)  # List of capabilities

    # Configuration
    default_config = Column(JSON, nullable=True)  # Default parameters
    supported_formats = Column(JSON, nullable=True)  # Supported audio formats
    max_file_size = Column(Integer, nullable=True)  # Max file size in bytes
    max_duration = Column(Integer, nullable=True)  # Max duration in seconds

    # Performance and cost
    processing_speed = Column(Float, nullable=True)  # Files per minute
    cost_per_minute = Column(Float, nullable=True)  # Cost per minute of audio
    accuracy_score = Column(Float, nullable=True)  # Model accuracy 0-1

    # Availability
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)  # Requires premium subscription

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<VoiceModel(id={self.id}, name={self.name}, provider={self.provider})>"


class SpeechSegment(Base):
    """Speech segment within a recording."""

    __tablename__ = "speech_segments"

    # Primary key
    id = Column(GUID(), primary_key=True, default=new_uuid)

    # Foreign key
    recording_id = Column(GUID(), ForeignKey("voice_recordings.id"), nullable=False)

    # Segment information
    start_time = Column(Float, nullable=False)  # seconds
    end_time = Column(Float, nullable=False)  # seconds
    duration = Column(Float, nullable=False)  # seconds

    # Content
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)  # 0-1

    # Speaker identification
    speaker_id = Column(String(50), nullable=True)
    speaker_confidence = Column(Float, nullable=True)  # 0-1

    # Analysis
    emotional_tone = Column(String(50), nullable=True)
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    words = Column(JSON, nullable=True)  # Array of word-level data

    def __repr__(self) -> str:
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"<SpeechSegment(id={self.id}, text='{preview}')>"

    @property
    def word_count(self) -> int:
        """Get word count of the segment."""
        return len(self.text.split()) if self.text else 0
