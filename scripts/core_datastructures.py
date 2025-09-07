from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# This is the common return envelope that every agent function will return.
class CommonReturnEnvelope(TypedDict):
    # 'ok' tells the orchestrator if the operation was successful.
    ok: bool
    # 'reason' provides a short note or error message.
    reason: str
    # 'updates' is a dictionary of key-value pairs to merge into the global state.
    updates: Dict[str, Any]
    # 'signals' are flags that the orchestrator uses for routing.
    signals: Dict[str, Any]
    # 'metrics' is an optional dictionary for performance data.
    metrics: Dict[str, Any]


# This is the global state for the entire agentic system.
# The 'messages' key will hold the conversation history.
# The 'order_details' will hold all the dynamic data for the current delivery.
# The 'audit_log' will track the actions of each agent.
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    order_details: dict
    audit_log: list