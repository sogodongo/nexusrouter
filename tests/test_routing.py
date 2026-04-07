import sys
sys.path.insert(0, ".")

from ingestion.sources.gmail_adapter import fetch_recent_emails
from agents.classifier import classify_event, ClassificationResult
from routing.rules_engine import apply_rules

# Test with real emails
envelopes = fetch_recent_emails(max_results=5)

print("=" * 70)
print("NEXUSROUTER ROUTING DECISIONS")
print("=" * 70)

for envelope in envelopes:
    classification = classify_event(envelope)
    routing        = apply_rules(classification)

    print(f"\nSubject  : {envelope.subject[:60]}")
    print(f"Classifier said → intent={classification.intent} "
          f"urgency={classification.urgency} "
          f"agent={classification.target_agent}")
    print(f"Router decided  → intent={routing['intent']} "
          f"urgency={routing['urgency']} "
          f"agent={routing['target_agent']}")
    print(f"HITL required   : {routing['require_hitl']}")
    print(f"Rules applied   : {routing['applied_rules']}")
    print("-" * 70)

# Also test with a synthetic low-confidence result to verify the
# low_confidence_human_review rule fires correctly
print("\n--- Synthetic low-confidence test ---\n")
synthetic = ClassificationResult(
    intent="billing_failure",
    urgency="P3",
    target_agent="CustomerResolutionAgent",
    confidence=0.45,
    reasoning="Test case for low confidence routing",
)
routing = apply_rules(synthetic)
print(f"Confidence  : {synthetic.confidence}")
print(f"Route to    : {routing['route_to']}")
print(f"HITL        : {routing['require_hitl']}")
print(f"Rules applied: {routing['applied_rules']}")
