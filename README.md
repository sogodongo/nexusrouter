# NexusRouter — Intelligent Workflow Orchestration Engine

A production-grade AI automation system that ingests business signals from multiple sources, classifies intent using GPT-4o, applies business rules, dispatches specialist agents to take real actions, and logs every decision with a full audit trail.

---

## What it does

An email arrives: *"My payment failed for order ORD-4401 and my service is down."*

NexusRouter:
1. Normalizes the email into a standard `EventEnvelope`
2. Classifies intent as `billing_failure` with urgency `P2` using GPT-4o
3. Applies business rules — Enterprise customer → confirm P2
4. Checks HITL gate — confidence 0.87, no human review needed
5. Dispatches `CustomerResolutionAgent`
6. Agent looks up CRM, checks payment status, issues refund, sends resolution email
7. Logs every step to the audit trail with full action history

Total time: ~10 seconds. Zero human involvement.

---

## Architecture
```
Gmail / Slack / Webhook → EventEnvelope normalizer → Redis Stream
                                                           ↓
                                              GPT-4o Classifier
                                                           ↓
                                           YAML Business Rules Engine
                                                           ↓
                                                    HITL Gate
                                              /         |         \
                                   Customer      Infra        Sales
                                   Resolution    Incident     Qualification
                                   Agent         Agent        Agent
                                              \         |         /
                                              PostgreSQL Audit Log
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design decisions.

---

## Stack

| Component | Technology |
|-----------|------------|
| Email ingestion | Gmail API + OAuth2 |
| Event queue | Redis Streams 7.2 |
| Normalization | Pydantic EventEnvelope |
| Classification | GPT-4o (structured JSON output) |
| Business rules | YAML rules engine |
| Agent framework | LangGraph ReAct |
| Audit store | PostgreSQL 15 |
| API | FastAPI |

---

## Quick start
```bash
git clone https://github.com/sogodongo/nexusrouter
cd nexusrouter
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY to .env
docker compose up -d
uvicorn api.main:app --reload --port 8001
```

---

## API endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Service health check |
| /webhook/gmail | POST | Gmail push notification receiver |
| /process | POST | Manual event submission |
| /events | GET | Recent events audit feed |
| /events/{id} | GET | Full event detail + action history |
| /metrics | GET | Throughput and agent distribution |

Interactive docs at `http://localhost:8001/docs`

---

## Processing a manual event
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Payment failed for order ORD-4401",
    "sender": "john@acmecorp.com",
    "body": "My payment failed and my service is interrupted.",
    "source": "manual"
  }'
```

---

## Project status

| Day | Component | Status |
|-----|-----------|--------|
| 1 | Project scaffold | Done |
| 2 | Gmail adapter + EventEnvelope | Done |
| 3 | Redis Streams + consumer groups | Done |
| 4 | GPT-4o classifier + entity extraction | Done |
| 5 | YAML business rules engine | Done |
| 6 | PostgreSQL audit logger | Done |
| 7 | CustomerResolutionAgent | Done |
| 8 | InfraIncidentAgent | Done |
| 9 | SalesQualificationAgent | Done |
| 10 | Main orchestrator | Done |
| 11 | FastAPI endpoints | Done |
| 12 | Documentation + release | Done |
