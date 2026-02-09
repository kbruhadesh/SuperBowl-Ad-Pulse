"""
Pydantic Schemas — Request/Response validation.

No business logic here. Just data shapes.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────
# Request Schemas
# ─────────────────────────────────────────────

class AnalyzeSegmentRequest(BaseModel):
    """Request to analyze a single video segment."""
    start_sec: int = Field(..., ge=0, description="Segment start time in seconds")
    end_sec: int = Field(..., gt=0, description="Segment end time in seconds")
    video_uri: Optional[str] = Field(None, description="Override Gemini video URI")
    business_name: str = Field("", description="Business name for ad context")
    business_type: str = Field("", description="Business type for ad context")
    
    @field_validator('end_sec')
    @classmethod
    def end_after_start(cls, v, info):
        if 'start_sec' in info.data and v <= info.data['start_sec']:
            raise ValueError('end_sec must be greater than start_sec')
        return v


class GenerateAdRequest(BaseModel):
    """Request to generate an ad for a specific event."""
    event_id: int = Field(..., description="Event ID from database")
    business_name: str = Field("", description="Business name for ad context")
    business_type: str = Field("", description="Business type for ad context")


# ─────────────────────────────────────────────
# Gemini Response Schema (Strict JSON contract)
# ─────────────────────────────────────────────

class GeminiEventResponse(BaseModel):
    """
    Expected JSON structure from Gemini.
    If Gemini returns invalid JSON, the segment is discarded.
    """
    event_type: str = Field(..., description="Type of event detected")
    intensity: str = Field("low", description="low|medium|high")
    summary: str = Field("", description="Short event description")
    crowd_reaction: str = Field("", description="Crowd response description")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score 0-1")
    
    @field_validator('intensity')
    @classmethod
    def validate_intensity(cls, v):
        allowed = {"low", "medium", "high"}
        if v.lower() not in allowed:
            return "low"
        return v.lower()
    
    @field_validator('confidence')
    @classmethod
    def clamp_confidence(cls, v):
        return max(0.0, min(1.0, float(v)))


# ─────────────────────────────────────────────
# Response Schemas
# ─────────────────────────────────────────────

class EventResponse(BaseModel):
    """Event data returned from API."""
    id: int
    start_sec: int
    end_sec: int
    event_type: str
    intensity: str
    summary: Optional[str]
    confidence: float
    score: float
    generate_ad: bool
    urgency: Optional[str]
    gemini_latency_ms: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdResponse(BaseModel):
    """Ad data returned from API."""
    id: int
    event_id: int
    ad_copy: str
    promo_suggestion: Optional[str]
    social_hashtags: Optional[str]
    urgency: str
    business_name: Optional[str]
    business_type: Optional[str]
    groq_latency_ms: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    """Combined result from analyze-segment endpoint."""
    event: EventResponse
    ad: Optional[AdResponse]
    decision_reason: str = Field(..., description="Why ad was/wasn't generated")


class DecisionResult(BaseModel):
    """Output from decision layer."""
    generate_ad: bool
    urgency: str  # "ignore", "soft", "aggressive"
    reason: str


class MetricsResponse(BaseModel):
    """Pipeline metrics for evaluation."""
    avg_gemini_latency_ms: Optional[float]
    avg_groq_latency_ms: Optional[float]
    total_segments: int
    segments_discarded: int
    ads_generated: int
    discard_rate: float
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    timestamp: datetime
