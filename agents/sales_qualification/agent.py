import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from agents.sales_qualification.prompts import SYSTEM_PROMPT
from agents.sales_qualification.tools import ALL_TOOLS

load_dotenv()

_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

_agent = create_react_agent(_llm, ALL_TOOLS)


def run_sales_qualification(
    inquiry_text: str,
    sender_email: str,
    company_name: str = "",
) -> dict:
    """
    Runs the SalesQualificationAgent on an inbound sales inquiry.
    Enriches, scores, routes, and schedules follow-up automatically.
    """
    input_text = f"""{SYSTEM_PROMPT}

Inbound sales inquiry received:

From: {sender_email}
Company: {company_name}

Message:
{inquiry_text}

Qualify this lead and complete all 6 steps."""

    print(f"\n[SalesQualificationAgent] Qualifying lead from {sender_email}")
    result = _agent.invoke({
        "messages": [HumanMessage(content=input_text)]
    })

    final_message = result["messages"][-1].content

    print("\n[SalesQualificationAgent] Tool calls made:")
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"  → {tc['name']}({list(tc['args'].keys())})")

    return {
        "agent":      "SalesQualificationAgent",
        "resolution": final_message,
        "status":     "completed",
    }
