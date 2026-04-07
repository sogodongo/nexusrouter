import sys
sys.path.insert(0, ".")

from ingestion.sources.gmail_adapter import fetch_recent_emails
from ingestion.orchestrator import process_event

# Fetch real emails and run each through the full pipeline
envelopes = fetch_recent_emails(max_results=3)

print(f"Processing {len(envelopes)} emails through NexusRouter...\n")

outcomes = []
for envelope in envelopes:
    outcome = process_event(envelope)
    outcomes.append(outcome)

print(f"\n{'='*60}")
print("NEXUSROUTER OUTCOMES")
print(f"{'='*60}")
for outcome in outcomes:
    print(f"\nEvent    : {outcome['event_id'][:16]}")
    print(f"Status   : {outcome['status']}")
    print(f"Intent   : {outcome.get('intent', 'N/A')}")
    print(f"Urgency  : {outcome.get('urgency', 'N/A')}")
    print(f"Agent    : {outcome.get('agent', 'N/A')}")
    print(f"Elapsed  : {outcome.get('elapsed_s')}s")
    if outcome.get("resolution"):
        print(f"Summary  : {outcome['resolution'][:150]}")
    print("-" * 60)
