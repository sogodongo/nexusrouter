import yaml
from pathlib import Path
from agents.classifier import ClassificationResult

RULES_PATH = "routing/rules/business_rules.yaml"


def _load_rules() -> list[dict]:
    with open(RULES_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])


def _condition_matches(condition: dict, result: ClassificationResult) -> bool:
    """
    Evaluates a single rule condition against a classification result.
    All specified condition fields must match for the rule to fire.
    """
    for key, value in condition.items():
        if key == "intent" and result.intent != value:
            return False
        if key == "urgency" and result.urgency != value:
            return False
        if key == "target_agent" and result.target_agent != value:
            return False
        if key == "confidence_lt" and result.confidence >= float(value):
            return False
        if key == "source":
            # source is on the envelope not the result — skip for now
            pass
    return True


def apply_rules(result: ClassificationResult) -> dict:
    """
    Evaluates all business rules against a classification result.
    Returns the original result enriched with any rule overrides applied.

    First matching rule wins — rules are evaluated in order so more
    specific rules should come before general ones in the YAML.
    """
    rules = _load_rules()
    applied_rules = []

    # Work with a mutable copy of the result fields
    overrides = {
        "intent":        result.intent,
        "urgency":       result.urgency,
        "target_agent":  result.target_agent,
        "confidence":    result.confidence,
        "require_hitl":  False,
        "route_to":      None,
    }

    for rule in rules:
        condition = rule.get("condition", {})
        action    = rule.get("action", {})

        if _condition_matches(condition, result):
            rule_name = rule.get("name", "unnamed")
            reason    = action.get("reason", "")
            print(f"[router] Rule matched: '{rule_name}' — {reason}")
            applied_rules.append(rule_name)

            if "override_urgency" in action:
                overrides["urgency"] = action["override_urgency"]
            if "override_agent" in action:
                overrides["target_agent"] = action["override_agent"]
            if "require_hitl" in action:
                overrides["require_hitl"] = action["require_hitl"]
            if "route_to" in action:
                overrides["route_to"] = action["route_to"]

            # First match wins — stop evaluating further rules
            break

    if not applied_rules:
        print(f"[router] No rules matched — using classifier decision as-is")

    return {
        "intent":        overrides["intent"],
        "urgency":       overrides["urgency"],
        "target_agent":  overrides["target_agent"],
        "confidence":    overrides["confidence"],
        "require_hitl":  overrides["require_hitl"],
        "route_to":      overrides["route_to"],
        "applied_rules": applied_rules,
        "entities":      result.entities,
        "reasoning":     result.reasoning,
        "secondary_intents": result.secondary_intents,
    }
