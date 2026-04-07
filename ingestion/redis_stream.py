import json
import redis
import os
from dotenv import load_dotenv
from ingestion.normalizer import EventEnvelope

load_dotenv()

STREAM_NAME   = "nexusrouter:events"
GROUP_NAME    = "nexusrouter-workers"
CONSUMER_NAME = "worker-1"
PEL_TIMEOUT_MS = 30_000


def _get_client() -> redis.Redis:
    return redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        decode_responses=True,
    )


def _ensure_consumer_group(client: redis.Redis):
    try:
        client.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
        print(f"[stream] Consumer group '{GROUP_NAME}' created.")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise


def push_event(envelope: EventEnvelope) -> str:
    client = _get_client()
    _ensure_consumer_group(client)

    dedup_key = f"nexusrouter:seen:{envelope.event_id}"
    if not client.set(dedup_key, "1", nx=True, ex=86400):
        print(f"[stream] Duplicate event {envelope.event_id[:16]} — skipping.")
        return ""

    entry_id = client.xadd(STREAM_NAME, {"data": envelope.model_dump_json()})
    print(f"[stream] Pushed event {envelope.event_id[:16]} → entry {entry_id}")
    return entry_id


def read_events(batch_size: int = 10, block_ms: int = 2000) -> list[tuple[str, EventEnvelope]]:
    client = _get_client()
    _ensure_consumer_group(client)

    results = client.xreadgroup(
        groupname=GROUP_NAME,
        consumername=CONSUMER_NAME,
        streams={STREAM_NAME: ">"},
        count=batch_size,
        block=block_ms,
    )

    if not results:
        return []

    events = []
    for _stream, messages in results:
        for entry_id, fields in messages:
            envelope = EventEnvelope.model_validate_json(fields["data"])
            events.append((entry_id, envelope))

    return events


def acknowledge_event(entry_id: str):
    client = _get_client()
    client.xack(STREAM_NAME, GROUP_NAME, entry_id)
    print(f"[stream] Acknowledged entry {entry_id}")


def get_stream_info() -> dict:
    client = _get_client()
    try:
        info    = client.xinfo_stream(STREAM_NAME)
        pending = client.xpending(STREAM_NAME, GROUP_NAME)
        return {
            "stream_length":  info["length"],
            "pending_count":  pending["pending"],
            "consumer_group": GROUP_NAME,
        }
    except Exception:
        return {"stream_length": 0, "pending_count": 0}
