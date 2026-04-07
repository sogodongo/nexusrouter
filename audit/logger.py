import json
from sqlalchemy import text
from audit.models import engine
from ingestion.normalizer import EventEnvelope
from agents.classifier import ClassificationResult


def log_event(
    envelope: EventEnvelope,
    classification: ClassificationResult,
    routing: dict,
) -> str:
    """
    Logs an incoming event with its classification and routing decision.
    Returns the event_id for linking action logs later.

    We log before any action is taken — if the agent crashes, we still
    have a record that the event was received and classified.
    """
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO event_log (
                event_id, source, sender, subject,
                intent, secondary_intents, urgency,
                target_agent, confidence, entities,
                reasoning, applied_rules, require_hitl,
                route_to, raw_text_preview
            ) VALUES (
                :event_id, :source, :sender, :subject,
                :intent, :secondary_intents, :urgency,
                :target_agent, :confidence, :entities,
                :reasoning, :applied_rules, :require_hitl,
                :route_to, :raw_text_preview
            )
            ON CONFLICT (event_id) DO NOTHING
        """), {
            "event_id":          envelope.event_id,
            "source":            envelope.source,
            "sender":            envelope.sender[:200],
            "subject":           envelope.subject[:500],
            "intent":            routing["intent"],
            "secondary_intents": json.dumps(routing.get("secondary_intents", [])),
            "urgency":           routing["urgency"],
            "target_agent":      routing["target_agent"],
            "confidence":        routing["confidence"],
            "entities":          json.dumps(routing.get("entities", {})),
            "reasoning":         routing.get("reasoning", ""),
            "applied_rules":     json.dumps(routing.get("applied_rules", [])),
            "require_hitl":      routing.get("require_hitl", False),
            "route_to":          routing.get("route_to"),
            "raw_text_preview":  envelope.normalized_text[:500],
        })
        conn.commit()

    print(f"[audit] Event logged: {envelope.event_id[:16]} "
          f"→ {routing['intent']} {routing['urgency']}")
    return envelope.event_id


def log_action(
    event_id: str,
    agent: str,
    action_type: str,
    action_input: dict,
    action_output: dict,
    status: str,
    error: str = None,
):
    """
    Logs an action taken by an agent against a specific event.
    status should be 'success', 'failed', or 'skipped'.
    """
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO action_log (
                event_id, agent, action_type,
                action_input, action_output, status, error
            ) VALUES (
                :event_id, :agent, :action_type,
                :action_input, :action_output, :status, :error
            )
        """), {
            "event_id":     event_id,
            "agent":        agent,
            "action_type":  action_type,
            "action_input":  json.dumps(action_input),
            "action_output": json.dumps(action_output),
            "status":       status,
            "error":        error,
        })
        conn.commit()

    print(f"[audit] Action logged: {agent} → {action_type} ({status})")


def get_recent_events(limit: int = 20) -> list[dict]:
    """Returns the most recent events for the audit dashboard."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT event_id, source, sender, subject,
                   intent, urgency, target_agent,
                   confidence, require_hitl, received_at
            FROM event_log
            ORDER BY received_at DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()
    return [dict(r._mapping) for r in rows]


def get_event_actions(event_id: str) -> list[dict]:
    """Returns all actions taken for a specific event."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT agent, action_type, status, error, executed_at
            FROM action_log
            WHERE event_id = :event_id
            ORDER BY executed_at ASC
        """), {"event_id": event_id}).fetchall()
    return [dict(r._mapping) for r in rows]
