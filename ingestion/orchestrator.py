import time
from ingestion.normalizer import EventEnvelope
from agents.classifier import classify_event
from routing.rules_engine import apply_rules
from audit.models import init_db
from audit.logger import log_event, log_action
from hitl.gate import check_hitl_required


def dispatch_to_agent(routing: dict, envelope: EventEnvelope) -> dict:
    """
    Routes the event to the correct specialist agent based on
    the routing decision. Returns the agent's resolution dict.
    """
    agent = routing["target_agent"]

    if agent == "CustomerResolutionAgent":
        from agents.customer_resolution.agent import run_customer_resolution
        # Extract order_id from entities if present
        order_id = routing.get("entities", {}).get("order_id")
        return run_customer_resolution(
            event_summary=envelope.normalized_text[:1000],
            customer_email=envelope.sender,
            order_id=order_id,
        )

    elif agent == "InfraIncidentAgent":
        from agents.infra_incident.agent import run_infra_incident
        return run_infra_incident(
            alert_text=envelope.normalized_text[:1000],
            source=envelope.source,
        )

    elif agent == "SalesQualificationAgent":
        from agents.sales_qualification.agent import run_sales_qualification
        # Try to extract company name from subject or entities
        company = routing.get("entities", {}).get("company_name", "")
        return run_sales_qualification(
            inquiry_text=envelope.normalized_text[:1000],
            sender_email=envelope.sender,
            company_name=company,
        )

    else:
        return {
            "agent":      agent,
            "resolution": f"No agent configured for: {agent}",
            "status":     "skipped",
        }


def process_event(envelope: EventEnvelope) -> dict:
    """
    Main orchestration pipeline — takes an EventEnvelope and runs it
    through the full NexusRouter pipeline end to end.

    Returns an OutcomeRecord with the full decision trail and result.
    """
    start = time.time()
    init_db()

    print(f"\n{'='*60}")
    print(f"[orchestrator] Processing: {envelope.subject[:50]}")
    print(f"{'='*60}")

    # Step 1: Classify
    classification = classify_event(envelope)

    # Step 2: Apply business rules
    routing = apply_rules(classification)

    # Step 3: Log event before any action
    log_event(envelope, classification, routing)

    # Step 4: HITL gate — check if human approval needed
    hitl_result = check_hitl_required(routing, envelope)
    if hitl_result["required"]:
        log_action(
            event_id=     envelope.event_id,
            agent=        "HITLGate",
            action_type=  "human_review_required",
            action_input= {"reason": hitl_result["reason"]},
            action_output={"status": "pending_human_review"},
            status=       "skipped",
        )
        elapsed = round(time.time() - start, 2)
        print(f"[orchestrator] HITL required — event queued for human review")
        return {
            "event_id":   envelope.event_id,
            "status":     "pending_human_review",
            "reason":     hitl_result["reason"],
            "routing":    routing,
            "elapsed_s":  elapsed,
        }

    # Step 5: Dispatch to agent
    try:
        agent_result = dispatch_to_agent(routing, envelope)
        status = agent_result.get("status", "completed")

        log_action(
            event_id=     envelope.event_id,
            agent=        routing["target_agent"],
            action_type=  "agent_execution",
            action_input= {"subject": envelope.subject},
            action_output={"resolution": agent_result.get("resolution", "")[:500]},
            status=       status,
        )

    except Exception as e:
        log_action(
            event_id=     envelope.event_id,
            agent=        routing["target_agent"],
            action_type=  "agent_execution",
            action_input= {"subject": envelope.subject},
            action_output={},
            status=       "failed",
            error=        str(e),
        )
        agent_result = {"resolution": f"Agent failed: {e}", "status": "failed"}

    elapsed = round(time.time() - start, 2)
    print(f"[orchestrator] Done in {elapsed}s — {routing['intent']} "
          f"{routing['urgency']} → {routing['target_agent']}")

    return {
        "event_id":   envelope.event_id,
        "status":     agent_result.get("status", "completed"),
        "intent":     routing["intent"],
        "urgency":    routing["urgency"],
        "agent":      routing["target_agent"],
        "resolution": agent_result.get("resolution", ""),
        "routing":    routing,
        "elapsed_s":  elapsed,
    }
