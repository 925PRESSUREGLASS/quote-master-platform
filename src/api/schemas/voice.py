"""Voice processing Pydantic schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator
from uuid import UUID

from src.api.models.voice import VoiceRecordingStatus, VoiceProcessingStatus, AudioFormat


class VoiceRecordingBase(BaseModel):
    """Base voice recording schema."""
    filename: str
    file_size: int
    file_format: AudioFormat
    duration_seconds: Optional[float] = None


class VoiceRecordingCreate(BaseModel):
    """Voice recording creation schema."""
    original_filename: str
    file_format: AudioFormat
    duration_seconds: Optional[float] = None
    device_info: Optional[Dict[str, Any]] = None
    retain_audio: bool = True


class VoiceRecordingUpdate(BaseModel):
    """Voice recording update schema."""
    transcription: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_public: Optional[bool] = None
    retain_audio: Optional[bool] = None


class VoiceRecordingResponse(VoiceRecordingBase):
    """Voice recording response schema."""
    id: UUID
    user_id: UUID
    original_filename: Optional[str]
    file_path: str
    mime_type: str
    sample_rate: Optional[int]
    bit_rate: Optional[int]
    channels: Optional[int]
    recorded_at: Optional[datetime]
    device_info: Optional[Dict[str, Any]]
    quality_score: Optional[float]
    status: VoiceRecordingStatus
    transcription: Optional[str]
    transcription_confidence: Optional[float]
    language_detected: Optional[str]
    speaker_count: Optional[int]
    emotional_analysis: Optional[Dict[str, Any]]
    content_categories: Optional[List[str]]
    keywords: Optional[List[str]]
    sentiment_score: Optional[float]
    ai_model_used: Optional[str]
    processing_duration: Optional[float]
    processing_cost: Optional[float]
    is_public: bool
    retain_audio: bool
    auto_delete_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    processed_at: Optional[datetime]
    is_processed: bool
    has_transcription: bool
    file_size_mb: float
    duration_formatted: str
    
    class Config:
        from_attributes = True


class VoiceProcessingJobBase(BaseModel):
    """Base voice processing job schema."""
    job_type: str
    parameters: Optional[Dict[str, Any]] = None


class VoiceProcessingJobCreate(VoiceProcessingJobBase):
    """Voice processing job creation schema."""
    recording_id: UUID
    priority: int = Field(5, ge=1, le=10)
    processing_config: Optional[Dict[str, Any]] = None


class VoiceProcessingJobUpdate(BaseModel):
    """Voice processing job update schema."""
    status: Optional[VoiceProcessingStatus] = None
    progress_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    current_step: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class VoiceProcessingJobResponse(VoiceProcessingJobBase):
    """Voice processing job response schema."""
    id: UUID
    user_id: UUID
    recording_id: UUID
    status: VoiceProcessingStatus
    priority: int
    processing_config: Optional[Dict[str, Any]]
    progress_percent: float
    current_step: Optional[str]
    steps_total: Optional[int]
    steps_completed: int
    result_data: Optional[Dict[str, Any]]
    output_files: Optional[List[str]]
    error_message: Optional[str]
    error_code: Optional[str]
    retry_count: int
    max_retries: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time: Optional[float]
    cpu_time: Optional[float]
    memory_peak: Optional[int]
    credits_used: Optional[float]
    cost_usd: Optional[float]
    worker_id: Optional[str]
    worker_version: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_completed: bool
    is_failed: bool
    can_retry: bool
    
    class Config:
        from_attributes = True


class VoiceProcessRequest(BaseModel):
    """Voice processing request schema."""
    recording_id: UUID
    job_types: List[str] = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = None
    priority: int = Field(5, ge=1, le=10)
    
    @validator('job_types')
    def validate_job_types(cls, v):
        valid_types = ['transcription', 'analysis', 'quote_generation', 'enhancement']
        for job_type in v:
            if job_type not in valid_types:
                raise ValueError(f'Invalid job type: {job_type}')
        return v


class VoiceTranscriptionRequest(BaseModel):
    """Voice transcription request schema."""
    recording_id: UUID
    model: Optional[str] = None
    language: Optional[str] = None
    prompt: Optional[str] = None
    response_format: str = Field("json", pattern="^(json|text|srt|verbose_json|vtt)$")
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)


class VoiceAnalysisRequest(BaseModel):
    """Voice analysis request schema."""
    recording_id: UUID
    analyze_emotion: bool = True
    analyze_sentiment: bool = True
    extract_keywords: bool = True
    categorize_content: bool = True
    detect_speakers: bool = True


class VoiceToQuoteRequest(BaseModel):
    """Voice to quote conversion request schema."""
    recording_id: UUID
    style: Optional[str] = None
    length: Optional[str] = Field(None, pattern="^(short|medium|long)$")
    tone: Optional[str] = None
    include_psychology: bool = True
    ai_model: Optional[str] = None


class VoiceUploadResponse(BaseModel):
    """Voice upload response schema."""
    upload_url: str
    recording_id: UUID
    expires_at: datetime
    max_file_size: int
    allowed_formats: List[str]


class VoiceModelResponse(BaseModel):
    """Voice model response schema."""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    version: str
    model_type: str
    provider: str
    capabilities: Optional[List[str]]
    supported_formats: Optional[List[str]]
    max_file_size: Optional[int]
    max_duration: Optional[int]
    processing_speed: Optional[float]
    cost_per_minute: Optional[float]
    accuracy_score: Optional[float]
    is_active: bool
    is_premium: bool
    
    class Config:
        from_attributes = True


class SpeechSegmentResponse(BaseModel):
    """Speech segment response schema."""
    id: UUID
    recording_id: UUID
    start_time: float
    end_time: float
    duration: float
    text: str
    confidence: Optional[float]
    speaker_id: Optional[str]
    speaker_confidence: Optional[float]
    emotional_tone: Optional[str]
    sentiment_score: Optional[float]
    words: Optional[List[Dict[str, Any]]]
    word_count: int
    
    class Config:
        from_attributes = True


class VoiceSearchRequest(BaseModel):
    """Voice recording search request schema."""
    query: Optional[str] = None
    status: Optional[VoiceRecordingStatus] = None
    has_transcription: Optional[bool] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: Optional[str] = Field(None, pattern="^(created_at|duration|quality_score)$")
    sort_order: Optional[str] = Field(None, pattern="^(asc|desc)$")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class VoiceSearchResponse(BaseModel):
    """Voice recording search response schema."""
    recordings: List[VoiceRecordingResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class VoiceStatistics(BaseModel):
    """Voice processing statistics schema."""
    total_recordings: int
    total_duration: float
    total_processed: int
    processing_success_rate: float
    average_processing_time: float
    most_common_language: Optional[str]
    recordings_this_month: int
    processing_cost_this_month: float