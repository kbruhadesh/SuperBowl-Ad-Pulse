"""
FastAPI Routes — ORCHESTRATION ONLY.

This layer:
- Routes requests
- Calls services
- Returns responses

This layer does NOT:
- Contain business logic
- Score events
- Make decisions
- Call LLM APIs directly

All of that is delegated to the appropriate modules.
"""
import json
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from ..db.database import get_db, reset_db
from ..db.models import Event, Ad, PipelineMetrics
from ..api.schemas import (
    AnalyzeSegmentRequest, GenerateAdRequest,
    EventResponse, AdResponse, AnalysisResult,
    MetricsResponse, HealthResponse
)
from ..core.scoring import calculate_event_score
from ..core.decision import make_decision
from ..services.gemini import GeminiService
from ..services.groq import GroqService


router = APIRouter(prefix="/api", tags=["api"])

# ── In-memory state for uploaded video ──
_state = {
    "video_uri": None,
    "uploading": False,
}
_state_lock = threading.Lock()


# ─────────────────────────────────────────────
# Video Upload
# ─────────────────────────────────────────────

@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload video to Gemini File API.
    Returns Gemini file URI for segment analysis.
    """
    with _state_lock:
        if _state["uploading"]:
            raise HTTPException(status_code=409, detail="Upload already in progress")
        _state["uploading"] = True
    
    try:
        # Save locally
        local_path = Path("uploaded_video.mp4")
        with open(local_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Upload to Gemini
        gemini = GeminiService()
        uri = gemini.upload_video(str(local_path))
        
        with _state_lock:
            _state["video_uri"] = uri
        
        return {"video_uri": uri, "status": "ready"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        with _state_lock:
            _state["uploading"] = False


@router.get("/upload-status")
def upload_status():
    """Check if video has been uploaded."""
    with _state_lock:
        return {
            "video_uri": _state["video_uri"],
            "uploading": _state["uploading"],
            "ready": _state["video_uri"] is not None and not _state["uploading"],
        }


# ─────────────────────────────────────────────
# Segment Analysis — THE MAIN PIPELINE
# ─────────────────────────────────────────────

@router.post("/analyze-segment", response_model=AnalysisResult)
def analyze_segment(
    request: AnalyzeSegmentRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze ONE video segment — the full pipeline:
    
    1. Gemini analyzes segment → JSON event
    2. Validate/normalize event
    3. Score event (scoring engine)
    4. Make decision (decision layer)
    5. IF decision.generate_ad → Groq generates ad
    6. Save to database
    7. Return result with explanation
    """
    # Determine video URI
    uri = request.video_uri
    if not uri:
        with _state_lock:
            uri = _state["video_uri"]
    if not uri:
        raise HTTPException(status_code=400, detail="No video uploaded. Upload first.")
    
    # ── Step 1: Gemini Analysis ──
    gemini = GeminiService()
    analysis = gemini.analyze_segment(uri, request.start_sec, request.end_sec)
    
    # If analysis failed, create event marked as discarded
    if not analysis.success:
        event = Event(
            start_sec=request.start_sec,
            end_sec=request.end_sec,
            event_type="unknown",
            intensity="low",
            summary=analysis.error or "Analysis failed",
            confidence=analysis.confidence,
            score=0.0,
            generate_ad=False,
            urgency="ignore",
            raw_response=analysis.raw_response,
            gemini_latency_ms=analysis.latency_ms,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return AnalysisResult(
            event=EventResponse.model_validate(event),
            ad=None,
            decision_reason=f"Segment discarded: {analysis.error}"
        )
    
    # ── Step 2: Score Event ──
    score, score_reasons = calculate_event_score(
        event_type=analysis.event_type,
        intensity=analysis.intensity,
        confidence=analysis.confidence,
        crowd_reaction=analysis.crowd_reaction,
    )
    
    # ── Step 3: Make Decision ──
    decision = make_decision(score, analysis.event_type)
    
    # ── Step 4: Create Event Record ──
    event = Event(
        start_sec=request.start_sec,
        end_sec=request.end_sec,
        event_type=analysis.event_type,
        intensity=analysis.intensity,
        summary=analysis.summary,
        crowd_reaction=analysis.crowd_reaction,
        confidence=analysis.confidence,
        score=score,
        generate_ad=decision.generate_ad,
        urgency=decision.urgency,
        raw_response=analysis.raw_response,
        gemini_latency_ms=analysis.latency_ms,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # ── Step 5: Generate Ad (if decision says so) ──
    ad_response = None
    if decision.generate_ad:
        groq = GroqService()
        ad_result = groq.generate_ad(
            event_type=analysis.event_type,
            urgency=decision.urgency,
            summary=analysis.summary,
            business_name=request.business_name,
            business_type=request.business_type,
        )
        
        if ad_result.success:
            ad = Ad(
                event_id=event.id,
                ad_copy=ad_result.ad_copy,
                promo_suggestion=ad_result.promo_suggestion,
                social_hashtags=json.dumps(ad_result.social_hashtags),
                urgency=decision.urgency,
                business_name=request.business_name,
                business_type=request.business_type,
                groq_latency_ms=ad_result.latency_ms,
            )
            db.add(ad)
            db.commit()
            db.refresh(ad)
            ad_response = AdResponse.model_validate(ad)
    
    # ── Step 6: Build Decision Explanation ──
    reason_parts = [decision.reason]
    reason_parts.append("Score breakdown: " + "; ".join(score_reasons))
    
    return AnalysisResult(
        event=EventResponse.model_validate(event),
        ad=ad_response,
        decision_reason=" | ".join(reason_parts)
    )


# ─────────────────────────────────────────────
# Read Endpoints
# ─────────────────────────────────────────────

@router.get("/events", response_model=list[EventResponse])
def get_events(db: Session = Depends(get_db)):
    """Get all detected events from database."""
    events = db.query(Event).order_by(Event.start_sec).all()
    return [EventResponse.model_validate(e) for e in events]


@router.get("/ads", response_model=list[AdResponse])
def get_ads(db: Session = Depends(get_db)):
    """Get all generated ads from database."""
    ads = db.query(Ad).order_by(Ad.created_at).all()
    return [AdResponse.model_validate(a) for a in ads]


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    """Get pipeline metrics for evaluation."""
    # Calculate metrics from events and ads
    total_segments = db.query(Event).count()
    segments_discarded = db.query(Event).filter(Event.generate_ad == False).count()
    ads_generated = db.query(Ad).count()
    
    avg_gemini = db.query(func.avg(Event.gemini_latency_ms)).scalar() or 0
    avg_groq = db.query(func.avg(Ad.groq_latency_ms)).scalar() or 0
    
    discard_rate = segments_discarded / total_segments if total_segments > 0 else 0
    
    return MetricsResponse(
        avg_gemini_latency_ms=round(avg_gemini, 2),
        avg_groq_latency_ms=round(avg_groq, 2),
        total_segments=total_segments,
        segments_discarded=segments_discarded,
        ads_generated=ads_generated,
        discard_rate=round(discard_rate, 4),
    )


# ─────────────────────────────────────────────
# Reset & Health
# ─────────────────────────────────────────────

@router.post("/reset")
def reset_all(db: Session = Depends(get_db)):
    """Clear all data and reset database."""
    reset_db()
    with _state_lock:
        _state["video_uri"] = None
    return {"status": "cleared", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    """Health check endpoint."""
    # Test database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"
    
    return HealthResponse(
        status="ok",
        database=db_status,
        timestamp=datetime.utcnow(),
    )


# ─────────────────────────────────────────────
# Legacy Compatibility (can be removed later)
# ─────────────────────────────────────────────

@router.post("/live-segment")
def live_segment(request: AnalyzeSegmentRequest, db: Session = Depends(get_db)):
    """Legacy endpoint - redirects to analyze-segment."""
    return analyze_segment(request, db)


@router.get("/ad-results")
def get_ad_results(db: Session = Depends(get_db)):
    """Legacy endpoint - redirects to /ads."""
    return get_ads(db)
