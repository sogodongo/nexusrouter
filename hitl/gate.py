from ingestion.normalizer import EventEnvelope


def check_hitl_required(routing: dict, envelope: EventEnvelope) -> dict:
    """
    Determines whether a human needs to approve this event before
    the agent takes action.

    Returns {"required": bool, "reason": str}
    """
    # Rule-based HITL flags take precedence
    if routing.get("require_hitl"):
        return {
            "required": True,
            "reason":   routing.get("route_to") or "Business rule requires human review",
        }

    # Low confidence — classifier wasn't sure
    if routing.get("confidence", 1.0) < 0.55:
        return {
            "required": True,
            "reason":   f"Low classifier confidence: {routing['confidence']}",
        }

    # Security incidents always need human eyes
    if routing.get("intent") == "security_incident":
        return {
            "required": True,
            "reason":   "Security incidents require human review before action",
        }

    return {"required": False, "reason": ""}
