from langchain_core.tools import tool


@tool
def get_crm_record(customer_email: str) -> dict:
    """Get customer account history, tier, and open tickets from CRM."""
    # Mock CRM data — replace with HubSpot API call in production
    mock_records = {
        "john@acmecorp.com": {
            "customer_id":   "C-9821",
            "name":          "John Smith",
            "tier":          "enterprise",
            "open_tickets":  0,
            "lifetime_value": 24000,
            "account_status": "active",
        },
        "sara@startup.io": {
            "customer_id":   "C-4421",
            "name":          "Sara Lee",
            "tier":          "starter",
            "open_tickets":  2,
            "lifetime_value": 480,
            "account_status": "active",
        },
    }
    return mock_records.get(customer_email, {
        "customer_id":   "C-UNKNOWN",
        "name":          "Unknown",
        "tier":          "starter",
        "open_tickets":  0,
        "lifetime_value": 0,
        "account_status": "active",
    })


@tool
def get_payment_status(order_id: str) -> dict:
    """Get payment status and failure reason for an order."""
    mock_payments = {
        "ORD-4401": {
            "order_id":      "ORD-4401",
            "amount":        299.00,
            "currency":      "USD",
            "status":        "failed",
            "failure_reason": "card_expired",
            "attempts":      1,
        },
        "ORD-8812": {
            "order_id":      "ORD-8812",
            "amount":        49.00,
            "currency":      "USD",
            "status":        "failed",
            "failure_reason": "insufficient_funds",
            "attempts":      2,
        },
    }
    return mock_payments.get(order_id, {
        "order_id": order_id,
        "status":   "not_found",
        "amount":   0,
    })


@tool
def issue_refund(order_id: str, amount: float) -> dict:
    """Issue a refund for an order via the payment processor."""
    if amount > 500:
        return {
            "status":  "requires_approval",
            "message": f"Refund of ${amount} exceeds auto-approval limit. Flagged for review.",
        }
    return {
        "status":    "success",
        "refund_id": f"REF-{order_id}-001",
        "amount":    amount,
        "message":   f"Refund of ${amount} issued successfully.",
    }


@tool
def apply_account_credit(customer_email: str, amount: float) -> dict:
    """Apply a credit to a customer account."""
    return {
        "status":  "success",
        "credit":  amount,
        "message": f"${amount} credit applied to {customer_email}",
    }


@tool
def send_resolution_email(customer_email: str, subject: str, body: str) -> dict:
    """Send a resolution email to the customer."""
    print(f"[mock] Email sent to {customer_email}: {subject}")
    return {"status": "sent", "to": customer_email, "subject": subject}


@tool
def create_support_ticket(
    customer_email: str, subject: str,
    description: str, priority: str
) -> dict:
    """Create a support ticket for manual follow-up."""
    ticket_id = f"TKT-{hash(customer_email + subject) % 10000:04d}"
    print(f"[mock] Ticket {ticket_id} created: {subject} ({priority})")
    return {"status": "created", "ticket_id": ticket_id, "priority": priority}


ALL_TOOLS = [
    get_crm_record,
    get_payment_status,
    issue_refund,
    apply_account_credit,
    send_resolution_email,
    create_support_ticket,
]
