"""
Gemini Service — PERCEPTION ONLY.

Gemini observes. It never decides.
All output is validated JSON.
Invalid responses are discarded.
"""
import json
import os
import time
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


@dataclass
class GeminiAnalysisResult:
    """Result from Gemini video analysis."""
    success: bool
    event_type: str = "unknown"
    intensity: str = "low"
    summary: str = ""
    crowd_reaction: str = ""
    confidence: float = 0.0
    raw_response: str = ""
    latency_ms: int = 0
    error: Optional[str] = None


class GeminiService:
    """
    Gemini video understanding service.
    
    Responsibilities:
    - Upload videos to Gemini File API
    - Analyze video segments with strict JSON output
    - Validate and normalize responses
    
    NOT responsible for:
    - Scoring (that's the scoring engine)
    - Decisions (that's the decision layer)
    - Ad generation (that's Groq)
    """
    
    MODEL = "models/gemini-2.5-flash"
    CONFIDENCE_THRESHOLD = 0.4  # Discard below this
    
    # Strict JSON prompt - forces Gemini to output exactly what we need
    ANALYSIS_PROMPT = """\
Analyze this video clip for significant sports events.

You MUST respond with ONLY a valid JSON object in this exact format:
{
  "event_type": "goal|touchdown|tackle|interception|fumble|penalty|big_play|injury|halftime|timeout|celebration|unknown",
  "intensity": "low|medium|high",
  "summary": "Brief description of what happened",
  "crowd_reaction": "Description of crowd response",
  "confidence": 0.0
}

Rules:
- event_type MUST be one of the listed values
- intensity MUST be "low", "medium", or "high"
- confidence is your certainty (0.0 to 1.0)
- If nothing significant happens, use event_type "unknown" with low confidence
- Output ONLY the JSON object, no other text
"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client."""
        self.api_key = api_key or self._get_api_key()
        self.client = genai.Client(api_key=self.api_key)
    
    @staticmethod
    def _get_api_key() -> str:
        """Get API key from environment."""
        key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError(
                "Missing Gemini API key. Set GOOGLE_API_KEY or GEMINI_API_KEY. "
                "Get a key at https://aistudio.google.com/apikey"
            )
        return key
    
    def upload_video(self, video_path: str) -> str:
        """
        Upload video to Gemini File API.
        
        Args:
            video_path: Local path to video file
            
        Returns:
            Gemini file URI for use in analysis
        """
        uploaded = self.client.files.upload(file=video_path)
        
        # Wait for processing
        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = self.client.files.get(name=uploaded.name)
        
        if uploaded.state.name != "ACTIVE":
            raise RuntimeError(f"Upload failed, state: {uploaded.state.name}")
        
        return uploaded.uri
    
    def analyze_segment(
        self,
        video_uri: str,
        start_sec: int,
        end_sec: int,
    ) -> GeminiAnalysisResult:
        """
        Analyze a video segment.
        
        This is the ONLY place Gemini is called for analysis.
        Output is validated JSON or marked as failed.
        
        Args:
            video_uri: Gemini file URI
            start_sec: Segment start time in seconds
            end_sec: Segment end time in seconds
            
        Returns:
            GeminiAnalysisResult with validated data or error
        """
        start_time = time.time()
        
        try:
            # Build video clip content
            video_metadata = types.VideoMetadata(
                start_offset=f"{start_sec}s",
                end_offset=f"{end_sec}s",
            )
            
            content = types.Content(
                parts=[
                    types.Part(
                        file_data=types.FileData(file_uri=video_uri),
                        video_metadata=video_metadata,
                    ),
                    types.Part(text=self.ANALYSIS_PROMPT),
                ]
            )
            
            # Make API call
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=content,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            raw_text = (response.text or "").strip()
            
            # Parse and validate JSON
            return self._parse_response(raw_text, latency_ms)
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return GeminiAnalysisResult(
                success=False,
                error=str(e),
                latency_ms=latency_ms,
            )
    
    def _parse_response(self, raw_text: str, latency_ms: int) -> GeminiAnalysisResult:
        """
        Parse and validate Gemini response.
        
        If parsing fails or confidence is too low, returns failure.
        """
        try:
            # Try to extract JSON from response
            # Sometimes Gemini wraps in markdown code blocks
            json_text = raw_text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]
            
            data = json.loads(json_text.strip())
            
            # Extract and normalize fields
            event_type = self._normalize_event_type(data.get("event_type", "unknown"))
            intensity = self._normalize_intensity(data.get("intensity", "low"))
            confidence = self._clamp_confidence(data.get("confidence", 0.0))
            
            # Check confidence threshold
            if confidence < self.CONFIDENCE_THRESHOLD:
                return GeminiAnalysisResult(
                    success=False,
                    event_type=event_type,
                    intensity=intensity,
                    summary=data.get("summary", ""),
                    crowd_reaction=data.get("crowd_reaction", ""),
                    confidence=confidence,
                    raw_response=raw_text,
                    latency_ms=latency_ms,
                    error=f"Confidence {confidence:.2f} below threshold {self.CONFIDENCE_THRESHOLD}",
                )
            
            return GeminiAnalysisResult(
                success=True,
                event_type=event_type,
                intensity=intensity,
                summary=data.get("summary", ""),
                crowd_reaction=data.get("crowd_reaction", ""),
                confidence=confidence,
                raw_response=raw_text,
                latency_ms=latency_ms,
            )
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return GeminiAnalysisResult(
                success=False,
                raw_response=raw_text,
                latency_ms=latency_ms,
                error=f"JSON parse error: {e}",
            )
    
    @staticmethod
    def _normalize_event_type(event_type: str) -> str:
        """Normalize event type to known enum value."""
        known_types = {
            "goal", "touchdown", "tackle", "interception", "fumble",
            "penalty", "big_play", "injury", "halftime", "timeout",
            "celebration", "unknown"
        }
        normalized = event_type.lower().strip().replace(" ", "_")
        return normalized if normalized in known_types else "unknown"
    
    @staticmethod
    def _normalize_intensity(intensity: str) -> str:
        """Normalize intensity to low/medium/high."""
        intensity_lower = intensity.lower().strip()
        if intensity_lower in {"low", "medium", "high"}:
            return intensity_lower
        return "low"
    
    @staticmethod
    def _clamp_confidence(confidence) -> float:
        """Clamp confidence to [0, 1]."""
        try:
            conf = float(confidence)
            return max(0.0, min(1.0, conf))
        except (ValueError, TypeError):
            return 0.0
