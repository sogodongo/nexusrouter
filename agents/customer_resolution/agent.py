import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from agents.customer_resolution.prompts import SYSTEM_PROMPT
from agents.customer_resolution.tools import ALL_TOOLS

load_dotenv()

_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

_agent = create_react_agent(_llm, ALL_TOOLS)


def run_customer_resolution(
    event_summary: str,
    customer_email: str,
    order_id: str = None,
) -> dict:
    """
    Runs the CustomerResolutionAgent on a billing or complaint event.
    Uses LangGraph's ReAct agent for multi-step tool calling.
    """
    input_text = f"""{SYSTEM_PROMPT}

Customer issue received:
{event_summary}

Customer email: {customer_email}
{f'Order ID: {order_id}' if order_id else ''}

Investigate and resolve this issue step by step."""

    print(f"\n[CustomerResolutionAgent] Starting resolution for {customer_email}")

    result = _agent.invoke({
        "messages": [HumanMessage(content=input_text)]
    })

    # Extract the final message from the agent
    final_message = result["messages"][-1].content

    # Print the reasoning trace
    print("\n[CustomerResolutionAgent] Reasoning trace:")
    for msg in result["messages"]:
        msg_type = type(msg).__name__
        if hasattr(msg, "content") and msg.content:
            print(f"  [{msg_type}]: {str(msg.content)[:200]}")

    return {
        "agent":      "CustomerResolutionAgent",
        "resolution": final_message,
        "status":     "completed",
    }
