"""
Database Models — SQLAlchemy ORM definitions.

Tables:
- events: Detected match events with scoring and confidence
- ads: Generated advertisements linked to events
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column, Integer, Float, String, Text, DateTime, 
    ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class EventType(str, PyEnum):
    """Normalized event types - strict enumeration."""
    GOAL = "goal"
    TOUCHDOWN = "touchdown"
    TACKLE = "tackle"
    INTERCEPTION = "interception"
    FUMBLE = "fumble"
    PENALTY = "penalty"
    BIG_PLAY = "big_play"
    INJURY = "injury"
    HALFTIME = "halftime"
    TIMEOUT = "timeout"
    CELEBRATION = "celebration"
    UNKNOWN = "unknown"


class IntensityLevel(str, PyEnum):
    """Intensity levels for events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UrgencyLevel(str, PyEnum):
    """Urgency levels for ad generation."""
    IGNORE = "ignore"
    SOFT = "soft"
    AGGRESSIVE = "aggressive"


class Event(Base):
    """
    Detected match events from Gemini video analysis.
    
    This is the core data structure that flows through the pipeline:
    Gemini → Normalization → Scoring → Decision → Ad Generation
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Time window
    start_sec = Column(Integer, nullable=False)
    end_sec = Column(Integer, nullable=False)
    
    # Event classification (from Gemini, normalized)
    event_type = Column(String(50), nullable=False, default="unknown")
    intensity = Column(String(20), nullable=False, default="low")
    
    # Gemini output
    summary = Column(Text, nullable=True)
    crowd_reaction = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    
    # Scoring engine output
    score = Column(Float, nullable=False, default=0.0)
    
    # Decision layer output
    generate_ad = Column(Boolean, nullable=False, default=False)
    urgency = Column(String(20), nullable=True)
    
    # Raw Gemini response (for debugging)
    raw_response = Column(Text, nullable=True)
    
    # Latency tracking
    gemini_latency_ms = Column(Integer, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    ads = relationship("Ad", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event id={self.id} type={self.event_type} score={self.score}>"


class Ad(Base):
    """
    Generated advertisements linked to events.
    
    Groq generates these based on event data and business context.
    """
    __tablename__ = "ads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to source event
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    
    # Generated content
    ad_copy = Column(Text, nullable=False)
    promo_suggestion = Column(Text, nullable=True)
    social_hashtags = Column(Text, nullable=True)  # JSON array stored as text
    
    # Decision context
    urgency = Column(String(20), nullable=False, default="soft")
    
    # Business context used
    business_name = Column(String(100), nullable=True)
    business_type = Column(String(100), nullable=True)
    
    # Latency tracking
    groq_latency_ms = Column(Integer, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    event = relationship("Event", back_populates="ads")
    
    def __repr__(self):
        return f"<Ad id={self.id} event_id={self.event_id} urgency={self.urgency}>"


class PipelineMetrics(Base):
    """
    Aggregated pipeline metrics for evaluation.
    One row per analysis session.
    """
    __tablename__ = "pipeline_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Session info
    video_uri = Column(String(500), nullable=True)
    
    # Latency metrics (in milliseconds)
    avg_gemini_latency_ms = Column(Float, nullable=True)
    avg_groq_latency_ms = Column(Float, nullable=True)
    
    # Quality metrics
    total_segments = Column(Integer, default=0)
    segments_discarded = Column(Integer, default=0)
    ads_generated = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<PipelineMetrics id={self.id} ads={self.ads_generated}>"
