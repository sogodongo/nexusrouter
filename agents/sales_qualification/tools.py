from langchain_core.tools import tool


@tool
def enrich_lead(email: str, company_name: str) -> dict:
    """Enrich a lead with firmographic data about their company."""
    mock_companies = {
        "acme": {
            "company":    "Acme Fintech Ltd",
            "industry":   "fintech",
            "employees":  450,
            "revenue":    "50M-100M",
            "location":   "Nairobi, Kenya",
            "tech_stack": ["AWS", "Python", "Kafka"],
        },
        "startup": {
            "company":    "QuickPay Startup",
            "industry":   "payments",
            "employees":  12,
            "revenue":    "Under 1M",
            "location":   "Lagos, Nigeria",
            "tech_stack": ["GCP", "Node.js"],
        },
    }
    # Simple lookup by domain
    domain = email.split("@")[-1].split(".")[0].lower()
    return mock_companies.get(domain, {
        "company":    company_name or "Unknown Company",
        "industry":   "unknown",
        "employees":  0,
        "revenue":    "unknown",
        "location":   "unknown",
        "tech_stack": [],
    })


@tool
def score_lead(enrichment_data: dict, inquiry_text: str) -> dict:
    """
    Score a lead against the Ideal Customer Profile criteria.
    Returns a score 0-100 and a tier classification.
    """
    score = 0

    # Company size scoring
    employees = enrichment_data.get("employees", 0)
    if employees >= 200:
        score += 35
    elif employees >= 50:
        score += 20
    elif employees >= 10:
        score += 10

    # Industry fit scoring
    high_fit_industries = ["fintech", "insurtech", "healthtech", "payments", "banking"]
    industry = enrichment_data.get("industry", "").lower()
    if any(ind in industry for ind in high_fit_industries):
        score += 30

    # Intent signal scoring
    high_intent_keywords = [
        "enterprise", "compliance", "api", "integration",
        "team", "procurement", "budget", "pilot"
    ]
    inquiry_lower = inquiry_text.lower()
    intent_matches = sum(1 for kw in high_intent_keywords if kw in inquiry_lower)
    score += min(intent_matches * 10, 35)

    if score >= 80:
        tier = "tier_1"
    elif score >= 50:
        tier = "tier_2"
    else:
        tier = "tier_3"

    return {"score": score, "tier": tier, "max_score": 100}


@tool
def get_sales_rep(lead_tier: str, industry: str) -> dict:
    """Get the best sales rep for a lead based on tier and industry."""
    routing = {
        "tier_1": {"rep": "Alice Kamau",     "email": "alice@company.com",  "slack": "@alice"},
        "tier_2": {"rep": "Brian Omondi",    "email": "brian@company.com",  "slack": "@brian"},
        "tier_3": {"rep": "Clara Wanjiku",   "email": "clara@company.com",  "slack": "@clara"},
    }
    rep = routing.get(lead_tier, routing["tier_3"])
    return {**rep, "tier": lead_tier, "industry": industry}


@tool
def update_crm_lead(
    email: str,
    company: str,
    score: int,
    tier: str,
    assigned_rep: str,
) -> dict:
    """Create or update a CRM lead record with qualification data."""
    lead_id = f"LEAD-{hash(email) % 9000 + 1000}"
    print(f"[mock] CRM lead {lead_id} updated: {company} score={score} tier={tier}")
    return {
        "lead_id":      lead_id,
        "status":       "updated",
        "score":        score,
        "tier":         tier,
        "assigned_rep": assigned_rep,
    }


@tool
def send_rep_notification(rep_email: str, lead_summary: str) -> dict:
    """Notify the assigned sales rep about a new qualified lead."""
    print(f"[mock] Slack DM to {rep_email}: New lead — {lead_summary[:80]}")
    return {"status": "sent", "to": rep_email}


@tool
def schedule_followup(
    rep_email: str,
    lead_email: str,
    delay_hours: int,
) -> dict:
    """Schedule a follow-up task for the sales rep."""
    print(f"[mock] Follow-up scheduled: {rep_email} → {lead_email} in {delay_hours}h")
    return {
        "status":       "scheduled",
        "rep":          rep_email,
        "lead":         lead_email,
        "delay_hours":  delay_hours,
    }


ALL_TOOLS = [
    enrich_lead,
    score_lead,
    get_sales_rep,
    update_crm_lead,
    send_rep_notification,
    schedule_followup,
]
