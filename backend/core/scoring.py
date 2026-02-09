"""
Event Scoring Engine — THE BRAIN.

Pure Python. No LLM. Deterministic. Unit-testable.

This replaces vibes with logic. Every score can be explained.
"""

# ─────────────────────────────────────────────
# Scoring Rules (Baseline Configuration)
# ─────────────────────────────────────────────

# Event type scores: positive = ad-worthy, negative = skip
EVENT_TYPE_SCORES = {
    # High-value events
    "goal": 4,
    "touchdown": 4,
    "interception": 3,
    "fumble": 3,
    "big_play": 3,
    
    # Medium-value events
    "penalty": 1,
    "tackle": 0,  # Neutral unless intensity is high
    "celebration": 2,
    
    # Low-value events
    "timeout": -1,
    "halftime": 1,  # Could be ad opportunity
    "injury": -1,   # Probably not good ad timing
    
    # Unknown/generic
    "unknown": -2,
}

# Intensity modifiers
INTENSITY_SCORES = {
    "high": 2,
    "medium": 1,
    "low": 0,
}

# Crowd reaction keywords → score boost
CROWD_KEYWORDS = {
    "loud": 2,
    "roar": 2,
    "cheer": 2,
    "wild": 2,
    "silent": -1,
    "boo": 1,  # Still engagement
    "gasp": 1,
}

# Confidence penalty threshold
CONFIDENCE_PENALTY_THRESHOLD = 0.5
CONFIDENCE_PENALTY = -3


def calculate_event_score(
    event_type: str,
    intensity: str,
    confidence: float,
    crowd_reaction: str = "",
) -> tuple[float, list[str]]:
    """
    Calculate event score from 0-10 with explanation.
    
    Args:
        event_type: Normalized event type (lowercase)
        intensity: "low", "medium", or "high"
        confidence: Gemini confidence score (0-1)
        crowd_reaction: Optional crowd description
        
    Returns:
        (score, reasons): Score clamped to 0-10 and list of scoring reasons
    """
    reasons = []
    score = 0.0
    
    # 1. Base score from event type
    event_type_lower = event_type.lower()
    base_score = EVENT_TYPE_SCORES.get(event_type_lower, -2)
    score += base_score
    reasons.append(f"Event type '{event_type_lower}': {base_score:+d}")
    
    # 2. Intensity modifier
    intensity_lower = intensity.lower()
    intensity_score = INTENSITY_SCORES.get(intensity_lower, 0)
    score += intensity_score
    if intensity_score != 0:
        reasons.append(f"Intensity '{intensity_lower}': {intensity_score:+d}")
    
    # 3. Confidence penalty
    if confidence < CONFIDENCE_PENALTY_THRESHOLD:
        score += CONFIDENCE_PENALTY
        reasons.append(f"Low confidence ({confidence:.2f}): {CONFIDENCE_PENALTY:+d}")
    
    # 4. Crowd reaction bonus
    if crowd_reaction:
        crowd_lower = crowd_reaction.lower()
        for keyword, bonus in CROWD_KEYWORDS.items():
            if keyword in crowd_lower:
                score += bonus
                reasons.append(f"Crowd '{keyword}': {bonus:+d}")
                break  # Only apply one crowd bonus
    
    # 5. Clamp to 0-10
    raw_score = score
    score = max(0.0, min(10.0, score))
    
    if raw_score != score:
        reasons.append(f"Clamped from {raw_score:.1f} to {score:.1f}")
    
    return score, reasons


def explain_score(
    event_type: str,
    intensity: str,
    confidence: float,
    crowd_reaction: str = "",
) -> str:
    """
    Generate human-readable score explanation.
    """
    score, reasons = calculate_event_score(
        event_type, intensity, confidence, crowd_reaction
    )
    
    explanation = f"Score: {score:.1f}/10\n"
    explanation += "Breakdown:\n"
    for reason in reasons:
        explanation += f"  • {reason}\n"
    
    return explanation


# ─────────────────────────────────────────────
# Unit Test Helpers
# ─────────────────────────────────────────────

def _test_scoring():
    """Basic sanity tests for scoring engine."""
    # Touchdown + high intensity = high score
    score, _ = calculate_event_score("touchdown", "high", 0.9)
    assert score >= 6, f"Touchdown+high should score >=6, got {score}"
    
    # Unknown + low confidence = low score
    score, _ = calculate_event_score("unknown", "low", 0.3)
    assert score <= 2, f"Unknown+low conf should score <=2, got {score}"
    
    # Goal with loud crowd = very high
    score, _ = calculate_event_score("goal", "high", 0.95, "crowd goes wild")
    assert score >= 8, f"Goal+loud crowd should score >=8, got {score}"
    
    print("All scoring tests passed!")


if __name__ == "__main__":
    _test_scoring()
    
    # Example usage
    print("\n" + "="*50)
    print("Example: Touchdown with high intensity")
    print(explain_score("touchdown", "high", 0.92, "crowd roars"))
    
    print("\n" + "="*50)
    print("Example: Generic tackle with low confidence")
    print(explain_score("tackle", "low", 0.35))
