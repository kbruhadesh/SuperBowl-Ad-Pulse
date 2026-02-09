"""
Decision Layer — NO AI HERE.

This layer is deterministic and explainable.
It takes a score and makes a binary decision with urgency level.

Rules:
- score < 4       → ignore (no ad)
- 4 ≤ score < 7   → soft ad
- score ≥ 7       → aggressive ad
"""
from dataclasses import dataclass
from typing import Literal


@dataclass
class Decision:
    """
    Decision output from the decision layer.
    This is what drives ad generation.
    """
    generate_ad: bool
    urgency: Literal["ignore", "soft", "aggressive"]
    reason: str


# ─────────────────────────────────────────────
# Decision Thresholds (Configurable)
# ─────────────────────────────────────────────

THRESHOLD_IGNORE = 4.0      # Below this: no ad
THRESHOLD_AGGRESSIVE = 7.0  # Above this: aggressive ad


def make_decision(score: float, event_type: str = "") -> Decision:
    """
    Make ad generation decision based on score.
    
    This is the ONLY place decisions are made.
    No magic. No AI. Just thresholds.
    
    Args:
        score: Event score from scoring engine (0-10)
        event_type: Optional event type for context in reason
        
    Returns:
        Decision object with generate_ad, urgency, and reason
    """
    if score < THRESHOLD_IGNORE:
        return Decision(
            generate_ad=False,
            urgency="ignore",
            reason=f"Score {score:.1f} below threshold ({THRESHOLD_IGNORE}). "
                   f"Event type: {event_type or 'unknown'}"
        )
    
    if score >= THRESHOLD_AGGRESSIVE:
        return Decision(
            generate_ad=True,
            urgency="aggressive",
            reason=f"Score {score:.1f} >= {THRESHOLD_AGGRESSIVE}: HIGH-VALUE moment. "
                   f"Event type: {event_type or 'unknown'}. Aggressive ad recommended."
        )
    
    # 4 ≤ score < 7
    return Decision(
        generate_ad=True,
        urgency="soft",
        reason=f"Score {score:.1f} in moderate range [{THRESHOLD_IGNORE}-{THRESHOLD_AGGRESSIVE}). "
               f"Event type: {event_type or 'unknown'}. Soft ad recommended."
    )


def explain_decision(score: float, event_type: str = "") -> str:
    """
    Generate human-readable decision explanation.
    """
    decision = make_decision(score, event_type)
    
    lines = [
        f"Decision: {'GENERATE AD' if decision.generate_ad else 'SKIP'}",
        f"Urgency: {decision.urgency.upper()}",
        f"Reason: {decision.reason}",
    ]
    
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Unit Test Helpers
# ─────────────────────────────────────────────

def _test_decision():
    """Basic sanity tests for decision layer."""
    # Low score = ignore
    decision = make_decision(2.5, "unknown")
    assert decision.generate_ad is False
    assert decision.urgency == "ignore"
    
    # Medium score = soft
    decision = make_decision(5.5, "penalty")
    assert decision.generate_ad is True
    assert decision.urgency == "soft"
    
    # High score = aggressive
    decision = make_decision(8.5, "touchdown")
    assert decision.generate_ad is True
    assert decision.urgency == "aggressive"
    
    # Edge cases
    decision = make_decision(4.0, "tackle")  # Exactly at threshold
    assert decision.generate_ad is True
    
    decision = make_decision(3.9, "tackle")  # Just below
    assert decision.generate_ad is False
    
    decision = make_decision(7.0, "goal")  # Exactly at aggressive
    assert decision.generate_ad is True
    assert decision.urgency == "aggressive"
    
    print("All decision tests passed!")


if __name__ == "__main__":
    _test_decision()
    
    # Example usage
    print("\n" + "="*50)
    print("Example: Score 8.5 (touchdown)")
    print(explain_decision(8.5, "touchdown"))
    
    print("\n" + "="*50)
    print("Example: Score 3.0 (unknown)")
    print(explain_decision(3.0, "unknown"))
    
    print("\n" + "="*50)
    print("Example: Score 5.5 (penalty)")
    print(explain_decision(5.5, "penalty"))
