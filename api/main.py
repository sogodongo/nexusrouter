import uuid
import json
import base64
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import ManualEventRequest, OutcomeResponse
from ingestion.normalizer import EventEnvelope
from ingestion.orchestrator import process_event
from audit.models import init_db, engine
from audit.logger import get_recent_events, get_event_actions
from sqlalchemy import text

app = FastAPI(
    title="NexusRouter API",
    description="Intelligent workflow orchestration — classify, decide, act.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "nexusrouter"}


@app.post("/webhook/gmail")
async def gmail_webhook(request: Request):
    """
    Receives Gmail push notifications via Google Cloud Pub/Sub.
    Google sends a base64-encoded message payload — we decode it
    and fetch the full email from the Gmail API.
    """
    body = await request.json()

    try:
        # Pub/Sub wraps the message in a data field encoded as base64
        message = body.get("message", {})
        data    = message.get("data", "")
        decoded = json.loads(base64.b64decode(data).decode("utf-8"))

        email_address = decoded.get("emailAddress", "")
        history_id    = decoded.get("historyId", "")

        print(f"[webhook] Gmail push received for {email_address} "
              f"historyId={history_id}")

        # In production: fetch the specific message using historyId
        # For now we acknowledge receipt
        return {"status": "received", "email": email_address}

    except Exception as e:
        print(f"[webhook] Failed to process Gmail push: {e}")
        return {"status": "error", "detail": str(e)}


@app.post("/process", response_model=OutcomeResponse)
def process_manual_event(request: ManualEventRequest):
    """
    Manually submit an event for processing.
    Useful for testing, replaying failed events, or processing
    signals from sources without native webhook support.
    """
    envelope = EventEnvelope(
        event_id=        str(uuid.uuid4()),
        source=          request.source,
        raw_payload=     request.model_dump(),
        normalized_text= f"Subject: {request.subject}\n\nFrom: {request.sender}\n\n{request.body}",
        sender=          request.sender,
        subject=         request.subject,
        received_at=     __import__("datetime").datetime.utcnow().isoformat(),
    )

    try:
        outcome = process_event(envelope)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return OutcomeResponse(**{
        k: v for k, v in outcome.items()
        if k in OutcomeResponse.model_fields
    })


@app.get("/events")
def list_events(limit: int = 20):
    """Returns the most recent events processed by NexusRouter."""
    events = get_recent_events(limit=limit)
    # Convert datetime objects to strings for JSON serialization
    for e in events:
        if hasattr(e.get("received_at"), "isoformat"):
            e["received_at"] = e["received_at"].isoformat()
    return {"count": len(events), "events": events}


@app.get("/events/{event_id}")
def get_event(event_id: str):
    """Returns full detail for a specific event including all actions taken."""
    events = get_recent_events(limit=100)
    event  = next((e for e in events if e["event_id"] == event_id), None)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if hasattr(event.get("received_at"), "isoformat"):
        event["received_at"] = event["received_at"].isoformat()

    actions = get_event_actions(event_id)
    for a in actions:
        if hasattr(a.get("executed_at"), "isoformat"):
            a["executed_at"] = a["executed_at"].isoformat()

    return {"event": event, "actions": actions}


@app.get("/metrics")
def get_metrics():
    """Returns throughput and performance metrics."""
    with engine.connect() as conn:
        total = conn.execute(
            text("SELECT COUNT(*) FROM event_log")
        ).scalar()

        by_intent = conn.execute(text("""
            SELECT intent, COUNT(*) as count
            FROM event_log
            GROUP BY intent
            ORDER BY count DESC
        """)).fetchall()

        by_agent = conn.execute(text("""
            SELECT target_agent, COUNT(*) as count
            FROM event_log
            GROUP BY target_agent
            ORDER BY count DESC
        """)).fetchall()

        hitl_count = conn.execute(text("""
            SELECT COUNT(*) FROM event_log WHERE require_hitl = true
        """)).scalar()

    return {
        "total_events":   total,
        "hitl_required":  hitl_count,
        "by_intent":      [dict(r._mapping) for r in by_intent],
        "by_agent":       [dict(r._mapping) for r in by_agent],
    }
