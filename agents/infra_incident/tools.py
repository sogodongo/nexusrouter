from langchain_core.tools import tool


@tool
def parse_alert_details(alert_text: str) -> dict:
    """Extract structured details from an infrastructure alert."""
    # In production this would use regex + LLM extraction
    # Mock returns realistic parsed data
    return {
        "affected_system": "terraform-infrastructure",
        "error_type":      "drift_detected",
        "severity":        "P1",
        "repository":      "sogodongo/pulsecommerce-data-platform",
        "workflow":        "Terraform Drift Check",
        "error_message":   "Infrastructure drift detected — state mismatch in production",
        "commit":          "b27ef9b",
    }


@tool
def get_runbook(system_name: str) -> dict:
    """Retrieve the runbook URL for a given system."""
    runbooks = {
        "terraform-infrastructure": "https://wiki.internal/runbooks/terraform-drift",
        "api-gateway":              "https://wiki.internal/runbooks/api-gateway-outage",
        "database":                 "https://wiki.internal/runbooks/database-recovery",
        "default":                  "https://wiki.internal/runbooks/general-incident",
    }
    url = runbooks.get(system_name, runbooks["default"])
    return {"system": system_name, "runbook_url": url}


@tool
def create_jira_ticket(
    summary: str,
    description: str,
    priority: str,
    affected_system: str,
) -> dict:
    """Create a Jira incident ticket."""
    ticket_id = f"INC-{hash(summary) % 9000 + 1000}"
    print(f"[mock] Jira ticket {ticket_id} created: {summary} ({priority})")
    return {
        "ticket_id":       ticket_id,
        "status":          "created",
        "priority":        priority,
        "affected_system": affected_system,
        "url":             f"https://jira.internal/browse/{ticket_id}",
    }


@tool
def page_oncall(
    incident_summary: str,
    severity: str,
    affected_system: str,
) -> dict:
    """Page the on-call engineer via PagerDuty."""
    print(f"[mock] PagerDuty alert sent: {severity} — {affected_system}")
    return {
        "status":       "paged",
        "severity":     severity,
        "incident_key": f"PD-{hash(incident_summary) % 9000 + 1000}",
        "message":      f"On-call engineer paged for {severity} incident on {affected_system}",
    }


@tool
def post_slack_incident(
    channel: str,
    incident_summary: str,
    ticket_id: str,
    runbook_url: str,
) -> dict:
    """Post an incident thread to a Slack channel."""
    print(f"[mock] Slack post in #{channel}: {incident_summary}")
    return {
        "status":   "posted",
        "channel":  channel,
        "message":  f"Incident thread posted: {ticket_id} | Runbook: {runbook_url}",
    }


ALL_TOOLS = [
    parse_alert_details,
    get_runbook,
    create_jira_ticket,
    page_oncall,
    post_slack_incident,
]
