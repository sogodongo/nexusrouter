import sys
sys.path.insert(0, ".")

from agents.customer_resolution.agent import run_customer_resolution

# Simulate a billing failure event
result = run_customer_resolution(
    event_summary="""Customer john@acmecorp.com reported that their payment
    for order ORD-4401 failed. They are requesting resolution and
    are frustrated that their service has been interrupted.""",
    customer_email="john@acmecorp.com",
    order_id="ORD-4401",
)

print("\n" + "=" * 70)
print("AGENT RESOLUTION SUMMARY")
print("=" * 70)
print(result["resolution"])
print("=" * 70)
