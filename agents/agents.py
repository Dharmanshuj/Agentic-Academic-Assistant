import os
import json
import operator
from typing import TypedDict, Annotated

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# ── Tools (via Spring Boot MCP Server) ────────────────────────────────────────
from tools.document_tool import search_documents
from tools.mcp_tool import (
    get_all_employees_salary_information,
    get_employee_by_id,
    get_attendance,
    get_salary_payment,
    get_all_employees_data,
    admin_get_monthly_metrics,
    get_all_attendance_for_employee,
)
from calculation.calculator import calculate_prorated_salary

# ── LLM ──────────────────────────────────────────────────────────────────────
_base_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.environ.get("GEMINI_API_KEY"),
)

# Payroll tools (served by Spring Boot via MCP)
PAYROLL_TOOLS = [
    get_employee_by_id,
    get_attendance,
    get_salary_payment,
    get_all_attendance_for_employee,
]

# Admin tools (served by Spring Boot via MCP)
ADMIN_TOOLS = [
    get_all_employees_data,
    get_all_employees_salary_information,
    admin_get_monthly_metrics,
]

# Policy tool
POLICY_TOOLS = [
    search_documents,
]

# ── Shared State ──────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    query: str
    emp_id: str
    final_answer: str
    next_node: str
    messages: Annotated[list, operator.add]


# ── Supervisor ────────────────────────────────────────────────────────────────
async def supervisor(state: AgentState):
    """Routes the query to the correct specialist node."""
    query = state["query"].lower()
    recent_history = state.get("messages", [])[-4:]
    history_text = "\n".join(
        [f"{type(m).__name__}: {m.content[:150]}" for m in recent_history]
    )

    prompt = f"""
You are an intelligent HR Agent Router.
Analyze the user's query and categorize their intent into exactly ONE of the following categories:

- policy_node  : Questions about company rules, HR policies, handbooks, time off, leave, benefits, or HOW salary components/calculations are determined.
- admin_node   : Requests to view data, salaries, or records for ALL employees or everyone.
- payroll_node : Questions about the user's personal attendance, present/absent days, specific salary, personal payslips, deductions, or compensation.

Recent Conversation History:
{history_text}

User Query: "{query}"

Respond with ONLY the exact category name. No quotes, no extra text.
"""
    response = await _base_llm.ainvoke([HumanMessage(content=prompt)])
    route = response.content.strip().strip('"').strip("'").lower()

    valid_routes = ["policy_node", "admin_node", "payroll_node"]
    if route in valid_routes:
        return {"next_node": route}

    # Fallback
    if state["emp_id"] == "ADMIN":
        return {"next_node": "admin_node"}
    return {"next_node": "payroll_node"}


# ── Agentic Payroll Node ──────────────────────────────────────────────────────
PAYROLL_SYSTEM_PROMPT = """You are an intelligent HR and Payroll Assistant.

The current demo year is 2026.

You have access to the following tools. Use them autonomously to answer the user's question:

- get_employee_by_id(emp_id)          → Employee profile (salary components, bank details)
- get_attendance(emp_id, month, year) → Attendance for a specific month
- get_salary_payment(attendance_id)   → Actual salary paid for a specific attendance record
- get_all_attendance_for_employee(emp_id, year) → All attendance records for the year

## Decision Logic
0. The authenticated employee ID is already provided in the conversation context. Never ask the user to provide their employee ID again.
1. ALWAYS start by calling `get_employee_by_id` to get the employee's profile.
2. If the user asks about a SPECIFIC month → call `get_attendance` then `get_salary_payment`.
3. If the user asks about all months or YTD → call `get_all_attendance_for_employee`, then call `get_salary_payment` for each record.
4. If attendance has no matching salary record, compute prorated salary:  base_salary × (present_days / total_days)
5. Combine all retrieved data and give a clear, professional answer.

Be concise. Do not reveal raw tool outputs. Format numbers with ₹ prefix.
"""

async def payroll_logic(state: AgentState):
    """
    Agentic payroll node: the LLM decides which tools to call and loops
    until it has sufficient information to produce a final answer.
    """
    emp_id = state["emp_id"]

    # Build the ReAct agent graph on-the-fly (lightweight, no extra state)
    llm_with_tools = _base_llm.bind_tools(PAYROLL_TOOLS)
    agent = create_react_agent(llm_with_tools, PAYROLL_TOOLS)

    # Inject emp_id into the query so the LLM always knows whose data to fetch
    enriched_query = (
        f"[Authenticated Employee ID: {emp_id}]\n"
        "Use this employee ID for payroll tools. Do not ask the user to provide it.\n\n"
        f"User question: {state['query']}"
    )

    messages = [
        SystemMessage(content=PAYROLL_SYSTEM_PROMPT),
        *state.get("messages", []),
        HumanMessage(content=enriched_query),
    ]

    result = await agent.ainvoke({"messages": messages})

    # The final AIMessage is the last message in the result
    final_message = result["messages"][-1]
    answer = final_message.content

    return {
        "final_answer": answer,
        "messages": [
            HumanMessage(content=state["query"]),
            AIMessage(content=answer),
        ],
    }


# ── Agentic Admin Node ────────────────────────────────────────────────────────
ADMIN_SYSTEM_PROMPT = """You are an HR Admin Dashboard Assistant.

The current demo year is 2026.

You have access to the following tools. Use them to answer the admin's question:

- get_all_employees_data()                          → Base info for all employees
- get_all_employees_salary_information()            → Comprehensive salary structure for all employees
- admin_get_monthly_metrics(month, year)            → Attendance + salary metrics for all employees

## Decision Logic
1. For questions about salary structure, salary breakdown, or compensation → call `get_all_employees_salary_information`.
2. For questions about ALL employees' general info (name, dept, designation) → call `get_all_employees_data`.
3. For questions about a specific month's payroll/attendance → call `admin_get_monthly_metrics(month, year)`.
4. For broad year-level questions → call `admin_get_monthly_metrics(month=None, year=<year>)`.
5. Combine data and provide a clear, tabular summary when there are multiple employees.

Be concise and professional.
"""

async def admin_logic(state: AgentState):
    """
    Agentic admin node: only accessible by ADMIN. LLM chooses tools autonomously.
    """
    if state["emp_id"] != "ADMIN":
        return {"final_answer": "Unauthorized Access. Only the ADMIN can query data for all employees."}

    llm_with_tools = _base_llm.bind_tools(ADMIN_TOOLS)
    agent = create_react_agent(llm_with_tools, ADMIN_TOOLS)

    messages = [
        SystemMessage(content=ADMIN_SYSTEM_PROMPT),
        *state.get("messages", []),
        HumanMessage(content=state["query"]),
    ]

    result = await agent.ainvoke({"messages": messages})
    final_message = result["messages"][-1]
    answer = final_message.content

    return {
        "final_answer": answer,
        "messages": [
            HumanMessage(content=state["query"]),
            AIMessage(content=answer),
        ],
    }


# ── Policy Node (RAG — no tool loop needed) ───────────────────────────────────
async def policy_logic(state: AgentState):
    """
    Retrieves information on how the salary components are determined/calculated and relevant HR policy documents via RAG and answers the question.
    """
    docs = search_documents.func(state["query"])

    prompt = f"""You are an HR Policy Assistant. Use the retrieved policy documents below to answer the user's question.

Documents:
{docs}

Question:
{state['query']}

Instructions:
- Answer strictly based on the provided documents.
- If the documents don't contain the answer, politely say so.
"""
    past_messages = state.get("messages", [])
    response = await _base_llm.ainvoke(past_messages + [HumanMessage(content=prompt)])

    return {
        "final_answer": response.content,
        "messages": [
            HumanMessage(content=state["query"]),
            AIMessage(content=response.content),
        ],
    }


# ── Graph Construction ────────────────────────────────────────────────────────
memory = MemorySaver()

def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor)
    workflow.add_node("payroll_node", payroll_logic)
    workflow.add_node("admin_node", admin_logic)
    workflow.add_node("policy_node", policy_logic)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_node"],
        {
            "payroll_node": "payroll_node",
            "admin_node": "admin_node",
            "policy_node": "policy_node",
        },
    )
    workflow.add_edge("payroll_node", END)
    workflow.add_edge("admin_node", END)
    workflow.add_edge("policy_node", END)

    return workflow.compile(checkpointer=memory)


# ── Entry Point ───────────────────────────────────────────────────────────────
async def run_salary_agent(query: str, emp_id: str, session_id: str):
    graph = create_graph()
    initial_state = {
        "query": query,
        "emp_id": emp_id,
        "final_answer": "",
        "next_node": "",
        "messages": [],
    }
    config = {"configurable": {"thread_id": session_id}}

    async for event in graph.astream(initial_state, config):
        for node_name, output in event.items():
            if "final_answer" in output:
                yield output["final_answer"]
