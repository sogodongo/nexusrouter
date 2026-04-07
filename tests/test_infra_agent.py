import sys
sys.path.insert(0, ".")

from agents.infra_incident.agent import run_infra_incident

# Use the real alert text from your inbox
alert_text = """
Run failed: Terraform Drift Check

Repository: sogodongo/pulsecommerce-data-platform
Workflow:   Terraform Drift Check
Branch:     main
Commit:     b27ef9b

The Terraform Drift Check workflow failed.
This indicates infrastructure drift — the actual state of cloud
resources no longer matches the Terraform state file.
Immediate investigation required to prevent configuration drift
from causing production issues.
"""

result = run_infra_incident(
    alert_text=alert_text,
    source="gmail"
)

print("\n" + "=" * 70)
print("INCIDENT RESOLUTION SUMMARY")
print("=" * 70)
print(result["resolution"])
print("=" * 70)
