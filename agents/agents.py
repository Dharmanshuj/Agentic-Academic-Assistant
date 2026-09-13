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

from langchain_core.runnables.config import RunnableConfig

# ── Tools (via Spring Boot MCP Server) ────────────────────────────────────────
from tools.document_tool import search_documents
from tools.mcp_tool import (
    get_all_students_academic_information,
    get_student_by_id,
    get_attendance,
    get_semester_results,
    get_all_students_data,
    admin_get_semester_metrics,
    get_all_attendance_for_student,
)


# ── LLM ──────────────────────────────────────────────────────────────────────
_base_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.environ.get("GEMINI_API_KEY"),
)

# Student tools (served by Spring Boot via MCP)
STUDENT_TOOLS = [
    get_student_by_id,
    get_attendance,
    get_semester_results,
    get_all_attendance_for_student,
    search_documents
]

# Admin tools (served by Spring Boot via MCP)
ADMIN_TOOLS = [
    get_all_students_data,
    get_all_students_academic_information,
    admin_get_semester_metrics,
]

# Academics/Curriculum tool
ACADEMICS_TOOLS = [
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
You are an intelligent Student Assistant Router for Dr. B.R. Ambedkar National Institute of Technology, Jalandhar (NIT Jalandhar).
Analyze the user's query and categorize their intent into exactly ONE of the following categories:

- academics_node : Questions about course curriculum, syllabus, timetables, academic policies, examination rules, grading system, or general institute information.
- admin_node     : Requests to view data or records for ALL students (only accessible by admin/faculty).
- student_node   : Questions about the user's personal profile, attendance, semester results, SGPA/CGPA, enrolled courses, or academic performance.

Recent Conversation History:
{history_text}

User Query: "{query}"

Respond with ONLY the exact category name. No quotes, no extra text.
"""
    response = await _base_llm.ainvoke([HumanMessage(content=prompt)])
    route = response.content.strip().strip('"').strip("'").lower()

    valid_routes = ["academics_node", "admin_node", "student_node"]
    if route in valid_routes:
        return {"next_node": route}

    # Fallback
    if state["emp_id"] == "ADMIN":
        return {"next_node": "admin_node"}
    return {"next_node": "student_node"}


# ── Agentic Student Node ──────────────────────────────────────────────────────
STUDENT_SYSTEM_PROMPT = """You are an intelligent Student Academic Assistant for Dr. B.R. Ambedkar National Institute of Technology, Jalandhar (NIT Jalandhar).

The current academic year is 2025-2026.

You have access to the following tools. Use them autonomously to answer the user's question:

- get_student_by_id()                    → Student profile (name, roll number, branch, semester, section, CGPA, etc.)
- get_attendance(month, year)            → Attendance for a specific month
- get_semester_results(semester)          → Results/grades for a specific semester
- get_all_attendance_for_student(year)   → All attendance records for the year
- search_documents(query)                → Search academic documents (syllabus, curriculum, timetables, policies)

## Academic Structure (NIT Jalandhar)
- Program: B.Tech (4 years / 8 semesters)
- Grading: 10-point CGPA scale (A+=10, A=9, B+=8, B=7, C+=6, C=5, D=4, F=0)
- SGPA = Σ(Grade Points × Credits) / Total Credits in Semester
- CGPA = Σ(SGPA × Semester Credits) / Total Credits Earned
- Minimum attendance required: 75%
- Detained if attendance < 75% in any subject

## Decision Logic
1. ALWAYS start by calling `get_student_by_id` to get the student's profile.
2. If the user asks about a SPECIFIC semester's results → call `get_semester_results(semester)`.
3. If the user asks about attendance → call `get_attendance(month, year)` or `get_all_attendance_for_student(year)`.
4. If asked about syllabus, curriculum, or timetable → call `search_documents(query)`.
5. Combine all retrieved data and give a clear, helpful answer.
6. ALWAYS address the user in the second person ("You", "Your"). Do NOT use "I" or "My" when referring to the user's data.
7. If the user asks a follow-up question, use the conversation history to provide conversational continuity.

Be concise and helpful. Do not reveal raw tool outputs.
"""

async def student_logic(state: AgentState, config: RunnableConfig):
    """
    Agentic student node: the LLM decides which tools to call and loops
    until it has sufficient information to produce a final answer.
    """
    emp_id = state["emp_id"]

    # Build the ReAct agent graph on-the-fly (lightweight, no extra state)
    llm_with_tools = _base_llm.bind_tools(STUDENT_TOOLS)
    agent = create_react_agent(llm_with_tools, STUDENT_TOOLS)

    # Note: student_id is injected via the graph config so tools can read it automatically.
    enriched_query = f"User question: {state['query']}"

    messages = [
        SystemMessage(content=STUDENT_SYSTEM_PROMPT),
        *state.get("messages", []),
        HumanMessage(content=enriched_query),
    ]

    result = await agent.ainvoke({"messages": messages}, config)

    # The final AIMessage is the last message in the result
    final_message = result["messages"][-1]
    answer = final_message.content if final_message.content else "I'm sorry, I couldn't formulate a proper response based on the available data."

    return {
        "final_answer": answer,
        "messages": [
            HumanMessage(content=state["query"]),
            AIMessage(content=answer),
        ],
    }


# ── Agentic Admin Node ────────────────────────────────────────────────────────
ADMIN_SYSTEM_PROMPT = """You are an Admin Dashboard Assistant for Dr. B.R. Ambedkar National Institute of Technology, Jalandhar (NIT Jalandhar).

The current academic year is 2025-2026.

You have access to the following tools. Use them to answer the admin's question:

- get_all_students_data()                            → Base info for all students (name, roll no, branch, semester)
- get_all_students_academic_information()            → Comprehensive academic records for all students
- admin_get_semester_metrics(semester, year)          → Attendance + academic metrics for all students

## Decision Logic
1. For questions about academic performance, CGPA, or grades → call `get_all_students_academic_information`.
2. For questions about ALL students' general info (name, branch, semester) → call `get_all_students_data`.
3. For questions about a specific semester's metrics/attendance → call `admin_get_semester_metrics(semester, year)`.
4. For broad year-level questions → call `admin_get_semester_metrics(semester=None, year=<year>)`.
5. Combine data and provide a clear, tabular summary when there are multiple students.
6. If the user asks to clarify or repeat a previous response, use the conversation history.

Be concise and professional.
"""

async def admin_logic(state: AgentState, config: RunnableConfig):
    """
    Agentic admin node: only accessible by ADMIN. LLM chooses tools autonomously.
    """
    if state["emp_id"] != "ADMIN":
        return {"final_answer": "Unauthorized Access. Only the ADMIN can query data for all students."}

    llm_with_tools = _base_llm.bind_tools(ADMIN_TOOLS)
    agent = create_react_agent(llm_with_tools, ADMIN_TOOLS)

    messages = [
        SystemMessage(content=ADMIN_SYSTEM_PROMPT),
        *state.get("messages", []),
        HumanMessage(content=state["query"]),
    ]

    result = await agent.ainvoke({"messages": messages}, config)
    for m in result["messages"]:
        print(f"[admin_logic debug] {type(m).__name__}: tool_calls={getattr(m, 'tool_calls', None)} content={m.content!r}")
    final_message = result["messages"][-1]
    answer = final_message.content if final_message.content else "I'm sorry, the admin query returned no text response."

    return {
        "final_answer": answer,
        "messages": [
            HumanMessage(content=state["query"]),
            AIMessage(content=answer),
        ],
    }


# ── Academics Node (RAG — no tool loop needed) ────────────────────────────────
async def academics_logic(state: AgentState, config: RunnableConfig):
    """
    Retrieves information about course curriculum, syllabus, timetables, and academic policies via RAG and answers the question.
    """
    docs = search_documents.func(state["query"])

    prompt = f"""You are an Academic Assistant for Dr. B.R. Ambedkar National Institute of Technology, Jalandhar (NIT Jalandhar). Use the retrieved academic documents below to answer the user's question.

Documents:
{docs}

Question:
{state['query']}

Instructions:
- Answer strictly based on the provided documents.
- If the documents don't contain the answer, politely say so.
- Refer to the data as curriculum/syllabus/academic policies as appropriate.
"""
    past_messages = state.get("messages", [])
    response = await _base_llm.ainvoke(past_messages + [HumanMessage(content=prompt)], config)

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
    workflow.add_node("student_node", student_logic)
    workflow.add_node("admin_node", admin_logic)
    workflow.add_node("academics_node", academics_logic)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_node"],
        {
            "student_node": "student_node",
            "admin_node": "admin_node",
            "academics_node": "academics_node",
        },
    )
    workflow.add_edge("student_node", END)
    workflow.add_edge("admin_node", END)
    workflow.add_edge("academics_node", END)

    return workflow.compile(checkpointer=memory)


def _profile_fallback_from_tools(config: RunnableConfig, query: str = "") -> str:
    """Build a useful profile response without using the LLM (for quota/rate-limit failures)."""
    try:
        profile = get_student_by_id.func(config)
        if isinstance(profile, dict):
            # No hardcoded sentence; return only fetched data.
            return json.dumps(profile, ensure_ascii=False)
        return str(profile)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


# ── Entry Point ───────────────────────────────────────────────────────────────
async def run_student_agent(query: str, emp_id: str, session_id: str):
    graph = create_graph()
    initial_state = {
        "query": query,
        "emp_id": emp_id,
        "final_answer": "",
        "next_node": "",
        "messages": [],
    }
    config = {"configurable": {"thread_id": session_id, "emp_id": emp_id}}

    try:
        async for event in graph.astream(initial_state, config):
            for node_name, output in event.items():
                if "final_answer" in output:
                    ans = output["final_answer"]
                    if not ans or not str(ans).strip():
                        yield "I apologize, but I received an empty response. Please try again."
                    else:
                        yield str(ans)
    except Exception as e:
        error_text = str(e)
        lowered = error_text.lower()
        if "resource_exhausted" in lowered or "quota" in lowered or "429" in lowered:
            yield _profile_fallback_from_tools(config, query)
        else:
            yield "An internal server error occurred while analyzing your request. Please try again."
