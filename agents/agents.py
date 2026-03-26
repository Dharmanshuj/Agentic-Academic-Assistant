EMPLOYEE_SYSTEM_PROMPT = """\
You are Pulse AI, an intelligent HR and Payroll assistant.
RULES:
1. NEVER guess or invent numbers...
2. The employee's ID is embedded in the user message...
...
"""


ADMIN_SYSTEM_PROMPT = """\
You are Pulse AI, an intelligent HR Admin assistant with full company-wide data access.
RULES:
1. NEVER guess or invent numbers...
2. For a list of all employees → call get_all_employees_data...
...
"""

import os
import asyncio
from typing import TypedDict, Annotated, Literal
import operator

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# 1. New Import for MCP
from langchain_mcp_adapters.client import MultiServerMCPClient
from tools.document_tool import search_documents

# ─────────────────────────────────────────────
# State & Setup
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    system_prompt: str
    tools: list  # Store tools in state or bind them at runtime

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", # Or your preferred version
    google_api_key=os.environ.get("GEMINI_API_KEY"),
)

# ─────────────────────────────────────────────
# Nodes (Modified for Dynamic Tools)
# ─────────────────────────────────────────────
async def call_model(state: AgentState):
    # Bind the tools provided by the MCP Client to the LLM
    llm_with_tools = llm.bind_tools(state["tools"])
    system_msg = SystemMessage(content=state["system_prompt"])
    response = await llm_with_tools.ainvoke([system_msg] + state["messages"])
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "__end__"

# ─────────────────────────────────────────────
# Graph Factory
# ─────────────────────────────────────────────
def create_agent_graph(all_tools):
    workflow = StateGraph(AgentState)
    
    # Pass the tools into the ToolNode
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(all_tools))

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=MemorySaver())

# ─────────────────────────────────────────────
# Main Entry Point with MCP Context
# ─────────────────────────────────────────────
async def run_salary_agent(query: str, emp_id: str, session_id: str):
    # Connect to the Spring Boot Server
    async with MultiServerMCPClient({
        "payroll_server": {
            "url": "http://localhost:8080/mcp/sse",
            "transport": "sse"
        }
    }) as mcp_client:
        
        # 2. Get Java Tools + Add local document tool
        java_tools = mcp_client.get_tools()
        all_tools = java_tools + [search_documents]
        
        # 3. Create graph with current tools
        graph = create_agent_graph(all_tools)
        
        config = {"configurable": {"thread_id": session_id}}
        system_prompt = ADMIN_SYSTEM_PROMPT if emp_id == "ADMIN" else EMPLOYEE_SYSTEM_PROMPT
        
        enriched_query = f"[Admin Query] {query}" if emp_id == "ADMIN" else f"[Employee ID: {emp_id}] {query}"

        initial_state = {
            "messages": [HumanMessage(content=enriched_query)],
            "system_prompt": system_prompt,
            "tools": all_tools # Pass tools into state
        }

        async for event in graph.astream_events(initial_state, config=config, version="v2"):
            if event.get("event") == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    if not (hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks):
                        yield chunk.content