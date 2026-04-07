import sys
sys.path.insert(0, ".")

from ingestion.sources.gmail_adapter import fetch_recent_emails
from agents.classifier import classify_event

envelopes = fetch_recent_emails(max_results=5)

print(f"Classifying {len(envelopes)} emails...\n")
print("=" * 70)

for envelope in envelopes:
    result = classify_event(envelope)
    print(f"\nSubject   : {envelope.subject[:60]}")
    print(f"From      : {envelope.sender[:50]}")
    print(f"Intent    : {result.intent}")
    print(f"Urgency   : {result.urgency}")
    print(f"Agent     : {result.target_agent}")
    print(f"Confidence: {result.confidence}")
    print(f"Reasoning : {result.reasoning}")
    if result.entities:
        print(f"Entities  : {result.entities}")
    print("-" * 70)
