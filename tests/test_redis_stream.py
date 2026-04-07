import sys
sys.path.insert(0, ".")

from ingestion.sources.gmail_adapter import fetch_recent_emails
from ingestion.redis_stream import push_event, read_events, acknowledge_event, get_stream_info

print("=== PUSHING EVENTS ===\n")
envelopes = fetch_recent_emails(max_results=3)
for envelope in envelopes:
    push_event(envelope)

info = get_stream_info()
print(f"\nStream length  : {info['stream_length']}")
print(f"Pending count  : {info['pending_count']}")

print("\n=== READING EVENTS ===\n")
events = read_events(batch_size=5)
print(f"Read {len(events)} events from stream\n")

for entry_id, envelope in events:
    print(f"Entry ID : {entry_id}")
    print(f"Source   : {envelope.source}")
    print(f"Subject  : {envelope.subject}")
    print(f"Sender   : {envelope.sender[:50]}")
    print("-" * 60)
    acknowledge_event(entry_id)

info = get_stream_info()
print(f"\nPending after ack: {info['pending_count']}")
