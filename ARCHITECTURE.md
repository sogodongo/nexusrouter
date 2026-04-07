# NexusRouter — System Architecture

This document explains the technical architecture of NexusRouter, the reasoning behind each major design decision, and the trade-offs considered during development.

---

## System overview

NexusRouter is a production-grade AI workflow orchestration engine. It ingests signals from multiple sources, classifies intent using an LLM, applies business rules, dispatches specialist agents to take real actions, and logs every decision with a full audit trail.

The core loop:
```
Signal arrives → Normalize → Classify (GPT-4o) → Apply rules (YAML)
             → HITL gate → Dispatch agent → Execute actions → Audit log
```

---

## Ingestion layer

### EventEnvelope — the universal input schema

Every signal source (Gmail, Slack, webhooks) produces data in a different format. The `EventEnvelope` Pydantic schema normalizes all sources into one standard shape before any downstream component sees the data.

**Decision:** Normalize at ingestion, not at classification.
**Reasoning:** If each downstream component handled source-specific formats, a new input source would require changes across the entire codebase. With `EventEnvelope`, adding a new source only requires writing one adapter.

### Gmail OAuth2 with token persistence

**Decision:** Use `InstalledAppFlow` with token pickle for development, Pub/Sub webhooks for production.
**Reasoning:** Polling is wasteful and slow. Gmail push notifications via Pub/Sub deliver new emails in under 1 second with zero polling overhead. The OAuth token is persisted so re-authentication only happens when the token expires.

### Redis Streams — reliable event queue

**Decision:** Redis Streams over Celery, SQS, or simple in-memory queues.
**Reasoning:** Redis Streams provide consumer groups (at-least-once delivery), stream replay for debugging, and sub-millisecond latency. Consumer group acknowledgement means a crashed worker never loses a message — the PEL timeout reclaims unacknowledged messages automatically.

**Trade-off:** Redis adds operational complexity. For very low volume (under 100 events/day), a simple PostgreSQL queue would suffice. Redis earns its complexity above that threshold.

---

## Classification layer

### GPT-4o classifier with structured output

**Decision:** LLM-based classification over traditional ML classifiers.
**Reasoning:** Traditional classifiers need thousands of labeled examples. GPT-4o classifies with zero training data using a well-engineered prompt. It handles novel signal types, multi-intent signals, and entity extraction in a single pass.

The `response_format={"type": "json_object"}` constraint ensures the output always parses cleanly. `temperature=0` keeps classifications deterministic.

**Trade-off:** LLM classification costs ~$0.002 per event and adds ~2s latency. For high-volume systems (10,000+ events/day), a fine-tuned smaller model would be more cost-effective. For moderate volumes, GPT-4o's accuracy advantage justifies the cost.

### Entity extraction in the classifier

**Decision:** Extract entities (order_id, customer_id, amounts) in the same pass as intent classification.
**Reasoning:** Making a separate extraction call doubles API cost and latency. The classifier prompt instructs GPT-4o to extract entities alongside classification — one call, complete structured output.

---

## Routing layer

### YAML business rules engine

**Decision:** Business rules in YAML, evaluated separately from AI classification.
**Reasoning:** Business logic changes frequently and is owned by operations teams, not engineers. A YAML rules file can be edited and hot-reloaded without a deployment. The first-match-wins evaluation order means more specific rules always take precedence over general ones.

**Trade-off:** Complex conditional logic (nested AND/OR) is verbose in YAML. The current rule evaluator supports flat conditions only. For complex rules, a proper rule DSL (like `python-rules-engine`) would be needed.

### HITL gate — three trigger conditions

Human-in-the-loop review is triggered by:
1. Business rule explicitly setting `require_hitl: true`
2. Classifier confidence below 0.55
3. Intent classified as `security_incident`

**Decision:** Check HITL before agent dispatch, not after.
**Reasoning:** An agent that takes an action and then asks for approval is not a HITL system — it's a post-hoc notification system. True HITL blocks execution until a human approves.

---

## Agent layer

### Three specialist agents over one monolithic agent

**Decision:** Separate `CustomerResolutionAgent`, `InfraIncidentAgent`, and `SalesQualificationAgent`.
**Reasoning:** A monolithic agent with all tools has a bloated system prompt and ambiguous tool selection. Specialist agents have focused prompts, tighter tool sets, and are independently testable and deployable.

**Trade-off:** Classification must be accurate — a mismatch routes to the wrong specialist. Mitigated by the HITL gate on low-confidence classifications.

### LangGraph ReAct agents

**Decision:** LangGraph `create_react_agent` over LangChain `AgentExecutor`.
**Reasoning:** LangGraph's ReAct implementation is the current standard in LangChain's ecosystem. It handles tool calling, observation, and multi-step reasoning cleanly with the modern tool-calling API.

### Mock tools with realistic data contracts

**Decision:** Build agents with mock tools, swap for real APIs later.
**Reasoning:** Agent logic and tool logic are independent. The agent doesn't care whether `issue_refund` calls a real Stripe API or returns mock data — it only cares about the response shape. Building with mocks allows full end-to-end testing without API credentials.

---

## Audit layer

### Log before action, not after

**Decision:** `log_event()` is called before agent dispatch.
**Reasoning:** If the agent crashes after taking an action, a post-action log would miss the event entirely. Pre-action logging ensures every signal is recorded regardless of what happens downstream. The `action_log.status` field records whether execution succeeded or failed.

### Two-table audit schema

`event_log` records the input — what signal arrived and what the system decided to do.
`action_log` records the output — what each agent actually did, linked by `event_id`.

This separation allows querying "show me all events that triggered agent X" independently from "show me all actions taken by agent X".

---

## API layer

### FastAPI with Pydantic response models

The `/process` endpoint accepts a `ManualEventRequest` and returns an `OutcomeResponse` — both validated by Pydantic. FastAPI auto-generates OpenAPI docs at `/docs` from these models.

### Gmail webhook receiver

The `/webhook/gmail` endpoint receives Gmail Pub/Sub push notifications. Google encodes the payload as base64 JSON — the endpoint decodes it and extracts the email address and history ID for processing.

---

## Known limitations and future work

- **Mock tools:** All agent tools use mock implementations. Production deployment requires real HubSpot, Stripe, Jira, PagerDuty, and Slack integrations.
- **Synchronous processing:** The `/process` endpoint blocks until the agent completes. For production, agent execution should be async with a job ID returned immediately.
- **Single consumer:** The Redis Stream consumer uses a single worker. Production needs multiple workers with PEL reclaim logic for fault tolerance.
- **Authentication:** The API has no authentication. Production requires API key or OAuth2.
- **Gmail polling vs push:** Development uses polling. Production should use Gmail Pub/Sub push notifications for real-time processing.
