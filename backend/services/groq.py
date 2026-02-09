"""
Groq Service — CREATIVITY ONLY.

Groq generates ads. It never sees raw video.
It never makes decisions about whether to generate ads.

Input: event_type, urgency, business_type, tone constraints
Output: ad_copy, hashtags, promo suggestion
"""
import json
import os
import time
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from dotenv import load_dotenv
from groq import Groq

# Load environment
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


@dataclass
class AdGenerationResult:
    """Result from Groq ad generation."""
    success: bool
    ad_copy: str = ""
    promo_suggestion: str = ""
    social_hashtags: List[str] = None
    latency_ms: int = 0
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.social_hashtags is None:
            self.social_hashtags = []


class GroqService:
    """
    Groq ad generation service.
    
    Responsibilities:
    - Generate ad copy based on event data
    - Generate promo suggestions
    - Generate hashtags
    
    NOT responsible for:
    - Video analysis (that's Gemini)
    - Deciding IF to generate ads (that's the decision layer)
    - Scoring events (that's the scoring engine)
    """
    
    MODEL = "llama-3.3-70b-versatile"
    MAX_TOKENS = 200  # Keep it tight
    
    # System prompt: focused, constrained, no fluff
    SYSTEM_PROMPT = """\
You are a sports marketing copywriter. Generate SHORT, PUNCHY ads.

Rules:
- ad_copy: 1-2 sentences MAX. Reference the game moment.
- promo_suggestion: A specific deal (%, $, or BOGO).
- social_hashtags: 2-3 relevant hashtags.
- Match urgency to tone: "aggressive"=exciting, "soft"=subtle.

Output ONLY valid JSON:
{
  "ad_copy": "Your ad text here",
  "promo_suggestion": "Specific promo deal",
  "social_hashtags": ["#hashtag1", "#hashtag2"]
}
"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Groq client."""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GROQ_API_KEY in environment")
        self.client = Groq(api_key=self.api_key)
    
    def generate_ad(
        self,
        event_type: str,
        urgency: str,
        summary: str = "",
        business_name: str = "",
        business_type: str = "",
    ) -> AdGenerationResult:
        """
        Generate ad for a game event.
        
        Args:
            event_type: Type of event (touchdown, goal, etc.)
            urgency: "soft" or "aggressive"
            summary: Event description from Gemini
            business_name: Business name for personalization
            business_type: Business type for context
            
        Returns:
            AdGenerationResult with ad copy and promo
        """
        start_time = time.time()
        
        try:
            # Build user prompt
            user_prompt = self._build_prompt(
                event_type, urgency, summary, business_name, business_type
            )
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=self.MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            raw_text = response.choices[0].message.content.strip()
            
            # Parse response
            return self._parse_response(raw_text, latency_ms)
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return AdGenerationResult(
                success=False,
                error=str(e),
                latency_ms=latency_ms,
            )
    
    def _build_prompt(
        self,
        event_type: str,
        urgency: str,
        summary: str,
        business_name: str,
        business_type: str,
    ) -> str:
        """Build user prompt for Groq."""
        biz = f"{business_name or 'Local Business'} ({business_type or 'general'})"
        
        return f"""\
Event: {event_type.upper()}
Description: {summary or 'Exciting game moment'}
Urgency: {urgency}
Business: {biz}

Generate an ad for this moment. JSON only."""
    
    def _parse_response(self, raw_text: str, latency_ms: int) -> AdGenerationResult:
        """Parse and validate Groq response."""
        try:
            data = json.loads(raw_text)
            
            return AdGenerationResult(
                success=True,
                ad_copy=data.get("ad_copy", ""),
                promo_suggestion=data.get("promo_suggestion", ""),
                social_hashtags=data.get("social_hashtags", []),
                latency_ms=latency_ms,
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            return AdGenerationResult(
                success=False,
                error=f"JSON parse error: {e}",
                latency_ms=latency_ms,
            )
