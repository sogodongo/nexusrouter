import sys
sys.path.insert(0, ".")

from ingestion.sources.gmail_adapter import fetch_recent_emails

envelopes = fetch_recent_emails(max_results=5)

print(f"\nFetched {len(envelopes)} envelopes\n")
for e in envelopes[:3]:
    print(f"Event ID  : {e.event_id}")
    print(f"Source    : {e.source}")
    print(f"Sender    : {e.sender}")
    print(f"Subject   : {e.subject}")
    print(f"Text preview: {e.normalized_text[:200]}")
    print("-" * 60)
