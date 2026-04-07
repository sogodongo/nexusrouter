import sys
sys.path.insert(0, ".")

from agents.sales_qualification.agent import run_sales_qualification

result = run_sales_qualification(
    inquiry_text="""Hi, I'm the Head of Compliance at Acme Fintech.
    We're looking for a regulatory intelligence solution for our team of 15 compliance analysts.
    We need API access and enterprise pricing. Our procurement team has approved a budget
    for this quarter. Can we schedule a demo?""",
    sender_email="compliance@acme.com",
    company_name="Acme Fintech Ltd",
)

print("\n" + "=" * 70)
print("SALES QUALIFICATION SUMMARY")
print("=" * 70)
print(result["resolution"])
print("=" * 70)
