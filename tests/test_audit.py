import sys
sys.path.insert(0, ".")

from ingestion.sources.gmail_adapter import fetch_recent_emails
from agents.classifier import classify_event
from routing.rules_engine import apply_rules
from audit.models import init_db
from audit.logger import log_event, log_action, get_recent_events, get_event_actions

# Initialize database tables
init_db()

# Run the full pipeline on 3 emails and log everything
envelopes = fetch_recent_emails(max_results=3)

logged_ids = []
for envelope in envelopes:
    classification = classify_event(envelope)
    routing        = apply_rules(classification)
    event_id       = log_event(envelope, classification, routing)
    logged_ids.append(event_id)

    # Simulate an agent action being logged
    log_action(
        event_id=     event_id,
        agent=        routing["target_agent"],
        action_type=  "classify_and_route",
        action_input= {"subject": envelope.subject},
        action_output={"intent": routing["intent"], "urgency": routing["urgency"]},
        status=       "success",
    )

# Verify audit trail
print(f"\n{'='*70}")
print("AUDIT TRAIL")
print(f"{'='*70}")

recent = get_recent_events(limit=5)
for event in recent:
    print(f"\nEvent    : {event['event_id'][:16]}")
    print(f"Subject  : {event['subject'][:50]}")
    print(f"Intent   : {event['intent']} | Urgency: {event['urgency']}")
    print(f"Agent    : {event['target_agent']}")
    print(f"HITL     : {event['require_hitl']}")

    actions = get_event_actions(event["event_id"])
    for action in actions:
        print(f"  Action : {action['agent']} → {action['action_type']} ({action['status']})")
