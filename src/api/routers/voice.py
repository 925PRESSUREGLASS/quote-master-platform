"""Voice processing router for Quote Master Pro."""

from typing import Optional, List
import os
from datetime import datetime

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    Query, 
    UploadFile, 
    File,
    BackgroundTasks
)
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.config import get_settings
from src.api.dependencies import (
    get_current_verified_user,
    check_voice_quota
)
from src.api.models.user import User
from src.api.models.voice import (
    VoiceRecording,
    VoiceProcessingJob,
    VoiceModel,
    SpeechSegment,
    VoiceRecordingStatus,
    VoiceProcessingStatus,
    AudioFormat
)
from src.api.schemas.voice import (
    VoiceRecordingResponse,
    VoiceProcessingJobResponse,
    VoiceProcessRequest,
    VoiceTranscriptionRequest,
    VoiceAnalysisRequest,
    VoiceToQuoteRequest,
    VoiceUploadResponse,
    VoiceModelResponse,
    SpeechSegmentResponse,
    VoiceSearchRequest,
    VoiceSearchResponse,
    VoiceStatistics
)

router = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=VoiceRecordingResponse, dependencies=[Depends(check_voice_quota)])
async def upload_voice_recording(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    retain_audio: bool = True,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Upload a voice recording for processing."""
    
    # Validate file type
    if file.content_type not in settings.allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed types: {settings.allowed_file_types}"
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
        )
    
    # Determine audio format
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    audio_format = AudioFormat.WAV  # Default
    
    format_mapping = {
        'wav': AudioFormat.WAV,
        'mp3': AudioFormat.MP3,
        'ogg': AudioFormat.OGG,
        'm4a': AudioFormat.M4A,
        'flac': AudioFormat.FLAC,
        'webm': AudioFormat.WEBM
    }
    
    if file_extension in format_mapping:
        audio_format = format_mapping[file_extension]
    
    # Generate unique filename
    import uuid
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    
    # Save file (in production, use cloud storage)
    upload_dir = "uploads/audio"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    # Create recording record
    recording = VoiceRecording(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(file_content),
        file_format=audio_format.value,
        mime_type=file.content_type,
        retain_audio=retain_audio,
        status=VoiceRecordingStatus.UPLOADED
    )
    
    db.add(recording)
    
    # Update user stats
    current_user.increment_voice_count()
    
    db.commit()
    db.refresh(recording)
    
    # Start background processing
    background_tasks.add_task(process_uploaded_audio, recording.id)
    
    return recording


@router.get("/recordings", response_model=List[VoiceRecordingResponse])
async def list_my_recordings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[VoiceRecordingStatus] = Query(None),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """List current user's voice recordings."""
    
    query = db.query(VoiceRecording).filter(VoiceRecording.user_id == current_user.id)
    
    if status:
        query = query.filter(VoiceRecording.status == status)
    
    recordings = query.order_by(VoiceRecording.created_at.desc()).offset(skip).limit(limit).all()
    
    return recordings


@router.post("/recordings/search", response_model=VoiceSearchResponse)
async def search_recordings(
    search_request: VoiceSearchRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Search voice recordings."""
    
    query = db.query(VoiceRecording).filter(VoiceRecording.user_id == current_user.id)
    
    # Apply filters
    if search_request.query:
        query = query.filter(
            VoiceRecording.transcription.ilike(f"%{search_request.query}%")
        )
    
    if search_request.status:
        query = query.filter(VoiceRecording.status == search_request.status)
    
    if search_request.has_transcription is not None:
        if search_request.has_transcription:
            query = query.filter(VoiceRecording.transcription.isnot(None))
        else:
            query = query.filter(VoiceRecording.transcription.is_(None))
    
    if search_request.min_duration:
        query = query.filter(VoiceRecording.duration_seconds >= search_request.min_duration)
    
    if search_request.max_duration:
        query = query.filter(VoiceRecording.duration_seconds <= search_request.max_duration)
    
    if search_request.date_from:
        query = query.filter(VoiceRecording.created_at >= search_request.date_from)
    
    if search_request.date_to:
        query = query.filter(VoiceRecording.created_at <= search_request.date_to)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    if search_request.sort_by:
        sort_column = getattr(VoiceRecording, search_request.sort_by, VoiceRecording.created_at)
        if search_request.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # Apply pagination
    recordings = query.offset(search_request.offset).limit(search_request.limit).all()
    
    return VoiceSearchResponse(
        recordings=recordings,
        total=total,
        limit=search_request.limit,
        offset=search_request.offset,
        has_more=search_request.offset + len(recordings) < total
    )


@router.get("/recordings/{recording_id}", response_model=VoiceRecordingResponse)
async def get_recording(
    recording_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get a specific voice recording."""
    
    recording = db.query(VoiceRecording).filter(
        VoiceRecording.id == recording_id,
        VoiceRecording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    return recording


@router.delete("/recordings/{recording_id}")
async def delete_recording(
    recording_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Delete a voice recording."""
    
    recording = db.query(VoiceRecording).filter(
        VoiceRecording.id == recording_id,
        VoiceRecording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Delete file if it exists
    if os.path.exists(recording.file_path):
        os.remove(recording.file_path)
    
    # Mark as deleted
    recording.status = VoiceRecordingStatus.DELETED
    db.commit()
    
    return {"message": "Recording deleted successfully"}


@router.post("/process", response_model=List[VoiceProcessingJobResponse])
async def process_recording(
    process_request: VoiceProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Start processing jobs for a voice recording."""
    
    # Check if recording exists and belongs to user
    recording = db.query(VoiceRecording).filter(
        VoiceRecording.id == process_request.recording_id,
        VoiceRecording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Create processing jobs
    jobs = []
    for job_type in process_request.job_types:
        job = VoiceProcessingJob(
            user_id=current_user.id,
            recording_id=recording.id,
            job_type=job_type,
            priority=process_request.priority,
            parameters=process_request.parameters
        )
        
        db.add(job)
        jobs.append(job)
    
    db.commit()
    
    # Start background processing
    for job in jobs:
        db.refresh(job)
        background_tasks.add_task(execute_voice_processing_job, job.id)
    
    return jobs


@router.post("/transcribe", response_model=VoiceProcessingJobResponse)
async def transcribe_recording(
    transcription_request: VoiceTranscriptionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Start transcription job for a recording."""
    
    # Check recording
    recording = db.query(VoiceRecording).filter(
        VoiceRecording.id == transcription_request.recording_id,
        VoiceRecording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Create transcription job
    job = VoiceProcessingJob(
        user_id=current_user.id,
        recording_id=recording.id,
        job_type="transcription",
        parameters={
            "model": transcription_request.model,
            "language": transcription_request.language,
            "prompt": transcription_request.prompt,
            "response_format": transcription_request.response_format,
            "temperature": transcription_request.temperature
        }
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start processing
    background_tasks.add_task(execute_voice_processing_job, job.id)
    
    return job


@router.post("/analyze", response_model=VoiceProcessingJobResponse)
async def analyze_recording(
    analysis_request: VoiceAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Start analysis job for a recording."""
    
    recording = db.query(VoiceRecording).filter(
        VoiceRecording.id == analysis_request.recording_id,
        VoiceRecording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    job = VoiceProcessingJob(
        user_id=current_user.id,
        recording_id=recording.id,
        job_type="analysis",
        parameters={
            "analyze_emotion": analysis_request.analyze_emotion,
            "analyze_sentiment": analysis_request.analyze_sentiment,
            "extract_keywords": analysis_request.extract_keywords,
            "categorize_content": analysis_request.categorize_content,
            "detect_speakers": analysis_request.detect_speakers
        }
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    background_tasks.add_task(execute_voice_processing_job, job.id)
    
    return job


@router.post("/voice-to-quote", response_model=VoiceProcessingJobResponse)
async def voice_to_quote(
    quote_request: VoiceToQuoteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Convert voice recording to quote."""
    
    recording = db.query(VoiceRecording).filter(
        VoiceRecording.id == quote_request.recording_id,
        VoiceRecording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Check if recording has transcription
    if not recording.has_transcription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording must be transcribed first"
        )
    
    job = VoiceProcessingJob(
        user_id=current_user.id,
        recording_id=recording.id,
        job_type="quote_generation",
        parameters={
            "style": quote_request.style,
            "length": quote_request.length,
            "tone": quote_request.tone,
            "include_psychology": quote_request.include_psychology,
            "ai_model": quote_request.ai_model
        }
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    background_tasks.add_task(execute_voice_processing_job, job.id)
    
    return job


@router.get("/jobs", response_model=List[VoiceProcessingJobResponse])
async def list_processing_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    job_type: Optional[str] = Query(None),
    status: Optional[VoiceProcessingStatus] = Query(None),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """List processing jobs."""
    
    query = db.query(VoiceProcessingJob).filter(VoiceProcessingJob.user_id == current_user.id)
    
    if job_type:
        query = query.filter(VoiceProcessingJob.job_type == job_type)
    
    if status:
        query = query.filter(VoiceProcessingJob.status == status)
    
    jobs = query.order_by(VoiceProcessingJob.created_at.desc()).offset(skip).limit(limit).all()
    
    return jobs


@router.get("/jobs/{job_id}", response_model=VoiceProcessingJobResponse)
async def get_processing_job(
    job_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get processing job details."""
    
    job = db.query(VoiceProcessingJob).filter(
        VoiceProcessingJob.id == job_id,
        VoiceProcessingJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.post("/jobs/{job_id}/retry", response_model=VoiceProcessingJobResponse)
async def retry_processing_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Retry a failed processing job."""
    
    job = db.query(VoiceProcessingJob).filter(
        VoiceProcessingJob.id == job_id,
        VoiceProcessingJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if not job.can_retry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be retried"
        )
    
    # Reset job status
    job.status = VoiceProcessingStatus.PENDING
    job.retry_count += 1
    job.error_message = None
    job.error_code = None
    job.progress_percent = 0.0
    job.current_step = None
    
    db.commit()
    
    # Start processing
    background_tasks.add_task(execute_voice_processing_job, job.id)
    
    return job


@router.get("/models", response_model=List[VoiceModelResponse])
async def list_voice_models(
    model_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List available voice processing models."""
    
    query = db.query(VoiceModel).filter(VoiceModel.is_active == True)
    
    if model_type:
        query = query.filter(VoiceModel.model_type == model_type)
    
    models = query.order_by(VoiceModel.name).all()
    
    return models


@router.get("/recordings/{recording_id}/segments", response_model=List[SpeechSegmentResponse])
async def get_speech_segments(
    recording_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get speech segments for a recording."""
    
    # Check recording ownership
    recording = db.query(VoiceRecording).filter(
        VoiceRecording.id == recording_id,
        VoiceRecording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    segments = db.query(SpeechSegment).filter(
        SpeechSegment.recording_id == recording_id
    ).order_by(SpeechSegment.start_time).all()
    
    return segments


@router.get("/statistics", response_model=VoiceStatistics)
async def get_voice_statistics(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get voice processing statistics for current user."""
    
    # Calculate statistics
    total_recordings = db.query(VoiceRecording).filter(
        VoiceRecording.user_id == current_user.id
    ).count()
    
    total_duration = db.query(func.sum(VoiceRecording.duration_seconds)).filter(
        VoiceRecording.user_id == current_user.id
    ).scalar() or 0.0
    
    total_processed = db.query(VoiceRecording).filter(
        VoiceRecording.user_id == current_user.id,
        VoiceRecording.status == VoiceRecordingStatus.PROCESSED
    ).count()
    
    processing_success_rate = (total_processed / total_recordings * 100) if total_recordings > 0 else 0.0
    
    # Average processing time from jobs
    avg_processing_time = db.query(func.avg(VoiceProcessingJob.processing_time)).filter(
        VoiceProcessingJob.user_id == current_user.id,
        VoiceProcessingJob.status == VoiceProcessingStatus.COMPLETED
    ).scalar() or 0.0
    
    # Most common language
    most_common_language = db.query(VoiceRecording.language_detected).filter(
        VoiceRecording.user_id == current_user.id,
        VoiceRecording.language_detected.isnot(None)
    ).group_by(VoiceRecording.language_detected).order_by(
        func.count(VoiceRecording.language_detected).desc()
    ).first()
    
    most_common_language = most_common_language[0] if most_common_language else None
    
    # This month statistics
    from datetime import datetime
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    recordings_this_month = db.query(VoiceRecording).filter(
        VoiceRecording.user_id == current_user.id,
        VoiceRecording.created_at >= start_of_month
    ).count()
    
    processing_cost_this_month = db.query(func.sum(VoiceProcessingJob.cost_usd)).filter(
        VoiceProcessingJob.user_id == current_user.id,
        VoiceProcessingJob.created_at >= start_of_month
    ).scalar() or 0.0
    
    return VoiceStatistics(
        total_recordings=total_recordings,
        total_duration=total_duration,
        total_processed=total_processed,
        processing_success_rate=round(processing_success_rate, 2),
        average_processing_time=round(avg_processing_time, 2),
        most_common_language=most_common_language,
        recordings_this_month=recordings_this_month,
        processing_cost_this_month=round(processing_cost_this_month, 2)
    )


# Background task functions
async def process_uploaded_audio(recording_id: str):
    """Process uploaded audio file."""
    # TODO: Implement audio processing
    # - Extract metadata (duration, format, etc.)
    # - Audio quality analysis
    # - Basic transcription if enabled
    pass


async def execute_voice_processing_job(job_id: str):
    """Execute a voice processing job."""
    # TODO: Implement job processing
    # - Route to appropriate AI service
    # - Update job progress
    # - Handle errors and retries
    pass