import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from agents.infra_incident.prompts import SYSTEM_PROMPT
from agents.infra_incident.tools import ALL_TOOLS

load_dotenv()

_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

_agent = create_react_agent(_llm, ALL_TOOLS)


def run_infra_incident(
    alert_text: str,
    source: str = "email",
) -> dict:
    """
    Runs the InfraIncidentAgent on an infrastructure alert.
    Parses the alert, creates a ticket, pages on-call, and posts Slack thread.
    """
    input_text = f"""{SYSTEM_PROMPT}

Infrastructure alert received via {source}:

{alert_text}

Handle this incident immediately following your decision process."""

    print(f"\n[InfraIncidentAgent] Processing alert...")
    result = _agent.invoke({
        "messages": [HumanMessage(content=input_text)]
    })

    final_message = result["messages"][-1].content

    print("\n[InfraIncidentAgent] Tool calls made:")
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"  → {tc['name']}({list(tc['args'].keys())})")

    return {
        "agent":      "InfraIncidentAgent",
        "resolution": final_message,
        "status":     "completed",
    }
