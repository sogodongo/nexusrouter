import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from ingestion.normalizer import EventEnvelope

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CLASSIFIER_SYSTEM_PROMPT = """You are NexusRouter's classifier. Your job is to analyze
incoming business signals and produce a structured routing decision.

Classify the signal into ONE of these intent categories:
- billing_failure       : payment failed, charge declined, invoice issue
- customer_complaint    : dissatisfied customer, bad experience, refund request
- sales_inquiry         : potential customer, pricing question, demo request
- infra_alert           : system down, error spike, performance degradation
- feature_request       : product feedback, new feature ask
- security_incident     : unauthorized access, data breach, suspicious activity
- account_closure       : customer wants to cancel or close account
- general_inquiry       : anything that doesn't fit above categories

Urgency levels:
- P1: Business critical — immediate action required (system down, security breach)
- P2: High — respond within 1 hour (billing failure, angry Enterprise customer)
- P3: Medium — respond within 4 hours (standard complaint, sales lead)
- P4: Low — respond next business day (general inquiry, feature request)

Target agents:
- CustomerResolutionAgent  : billing, complaints, refunds, account issues
- InfraIncidentAgent       : system alerts, errors, performance issues
- SalesQualificationAgent  : sales inquiries, demos, pricing questions

Rules:
- Extract any entities mentioned: customer_id, order_id, amount, error_codes, product names
- If multiple intents are present, list the primary and up to 2 secondary intents
- confidence is your certainty in the classification (0.0 to 1.0)
- reasoning must be one sentence explaining the primary classification
- Respond ONLY with valid JSON matching the schema. No prose outside the JSON."""

CLASSIFIER_USER_TEMPLATE = """Classify this incoming signal:

Source: {source}
Subject: {subject}
From: {sender}

Content:
{normalized_text}"""


class ClassificationResult(BaseModel):
    intent:           str
    secondary_intents: list[str] = []
    urgency:          str
    target_agent:     str
    confidence:       float = Field(ge=0.0, le=1.0)
    entities:         dict = {}
    reasoning:        str


def classify_event(envelope: EventEnvelope) -> ClassificationResult:
    """
    Classifies an EventEnvelope using GPT-4o and returns a structured
    routing decision.

    Temperature 0 keeps classifications deterministic — the same email
    should always get the same classification.
    """
    user_message = CLASSIFIER_USER_TEMPLATE.format(
        source=         envelope.source,
        subject=        envelope.subject,
        sender=         envelope.sender,
        normalized_text=envelope.normalized_text[:2000],
    )

    print(f"[classifier] Classifying: {envelope.subject[:60]}...")

    response = _client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    result = ClassificationResult(**data)

    print(f"[classifier] → intent={result.intent} urgency={result.urgency} "
          f"agent={result.target_agent} confidence={result.confidence}")

    return result
