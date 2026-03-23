import os
from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# Import your tools and calculator
from tools.document_tool import search_documents
import re
from tools.database_tool import (
    get_employee_by_id,
    get_attendance,
    get_salary_payment
)
from calculation.calculator import calculate_prorated_salary

# Initialize LLM with REST transport to avoid DNS/GRPC issues
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", 
    google_api_key=os.environ.get("GEMINI_API_KEY")
)

class AgentState(TypedDict):
    query: str
    emp_id: str
    final_answer: str
    next_node: str

# --- Node Logic ---

# async def supervisor(state: AgentState):
#     """Decides what response to give for the user query."""
#     prompt = (
#         f"You are a helpful HR and Payroll assistant. Categorize this user request: '{state['query']}'.\n"
#         "Respond with the data of employee:\n"
#     )
    
#     response = await llm.ainvoke([HumanMessage(content=prompt)])
#     route = response.content.strip().lower()
    
    # Mapping logic to ensure exact node names
    # if "greeting" in route:
    #     return {"next_node": "greeting_node"}
    # elif "payroll" in route:
    #     return {"next_node": "payroll_node"}
    # elif "policy" in route:
    #     return {"next_node": "policy_node"}
    # else:
    #     return {"next_node": "out_of_scope"}

async def supervisor(state: AgentState):
    query = state["query"].lower()
    
    # Automatically route all ADMIN queries to the dedicated admin interface
    if state["emp_id"] == "ADMIN":
        return {"next_node": "admin_node"}
        
    if "all employee" in query or "everyone" in query:
        return {"next_node": "admin_node"}
        
    return {"next_node": "payroll_node"}


# async def greeting_logic(state: AgentState):
#     return {"final_answer": "Hello! I am your HR & Payroll assistant. How can I help you with your salary or policy queries today?"}

# async def payroll_logic(state: AgentState):
#     # Call the tool using .ainvoke()
#     record = await get_employee_by_id.ainvoke({"emp_id": state["emp_id"]})
    
#     if not record or "base" not in record:
#         return {"final_answer": "I couldn't find your payroll records. Please contact HR."}

#     result = calculate_prorated_salary(
#         base_salary=record["base"], 
#         total_days=record["total"], 
#         present_days=record["present"]
#     )
    
#     return {"final_answer": f"Your calculated salary is {result['amount']} (Formula: {result['formula']})."}


# async def payroll_logic(state: AgentState):
#     record = await get_employee_by_id.ainvoke({
#         "emp_id": state["emp_id"]
#     })

#     if not record:
#         return {"final_answer": "I couldn't find your employee information. Please contact HR."}

#     employee_data = "\n".join([f"{k}: {v}" for k, v in record.items()])

#     prompt = f"""
# You are an intelligent HR and Payroll assistant.

# Here is the employee's salary data:
# {employee_data}

# User question:
# {state['query']}

# Instructions:
# - Answer ONLY based on the given data
# - If user asks meaning (like EPF, TDS), explain clearly
# - If user asks salary → give correct numbers
# - Be concise and professional
# """

#     response = await llm.ainvoke([HumanMessage(content=prompt)])

#     return {"final_answer": response.content}


import re
from tools.database_tool import (
    get_employee_by_id,
    get_attendance,
    get_salary_payment
)

async def payroll_logic(state: AgentState):

    # Step 1: Employee
    employee = await get_employee_by_id.ainvoke({
        "emp_id": state["emp_id"]
    })

    if not employee:
        return {"final_answer": "I couldn't find your employee information. Please contact HR."}

    # Step 2: Extract month/year from query
    query = state["query"].lower()

    month_map = {
        "january": 1, "february": 2, "march": 3,
        "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9,
        "october": 10, "november": 11, "december": 12
    }

    month = None
    for m, num in month_map.items():
        if m in query:
            month = num

    year = 2026  # demo default

    attendance = None
    salary = None

    if month:
        attendance = await get_attendance.ainvoke({
            "emp_id": state["emp_id"],
            "month": month,
            "year": year
        })

        if attendance:
            salary = await get_salary_payment.ainvoke({
                "attendance_id": attendance["attendance_id"]
            })
# --- Step 4: Format Data (MINIMAL CHANGE from your original logic) ---
    def format_data(data: dict, title: str):
        if not data:
            return f"{title}: Not available"
        return f"{title}:\n" + "\n".join([f"{k}: {v}" for k, v in data.items()])

    employee_data = format_data(employee, "Employee Data")
    attendance_data = format_data(attendance, "Attendance Data")
    salary_data = format_data(salary, "Salary Data")
    # Step 3: Build context for LLM
    prompt = f"""
You are an intelligent HR and Payroll assistant.

Here is the employee's salary data:
{employee_data}

{attendance_data}

{salary_data}

User question:
{state['query']}

Instructions:
- Answer ONLY based on the given data
- If user asks attendance → use attendance data
- If user asks meaning (like EPF, TDS), explain clearly
- If user asks salary → use salary data→ give correct numbers
- If explaining deductions → combine attendance + salary
- Be concise and professional
"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {"final_answer": response.content}

# def create_graph():
#     workflow = StateGraph(AgentState)
    
#     # Add all nodes
#     workflow.add_node("supervisor", supervisor)
#     workflow.add_node("greeting_node", greeting_logic)
#     workflow.add_node("payroll_node", payroll_logic)
#     workflow.add_node("policy_node", policy_logic)
#     workflow.add_node("out_of_scope", out_of_scope_logic)
    
#     workflow.set_entry_point("supervisor")
    
#     # Define routing
#     workflow.add_conditional_edges(
#         "supervisor",
#         lambda state: state["next_node"],
#         {
#             "greeting_node": "greeting_node",
#             "payroll_node": "payroll_node",
#             "policy_node": "policy_node",
#             "out_of_scope": "out_of_scope"
#         }
#     )
    
#     # All nodes lead to the end
#     workflow.add_edge("greeting_node", END)
#     workflow.add_edge("payroll_node", END)
#     workflow.add_edge("policy_node", END)
#     workflow.add_edge("out_of_scope", END)
    
#     return workflow.compile()

# --- Execution Entry Point ---

# --- Graph Construction ---
def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor)
    workflow.add_node("payroll_node", payroll_logic)

    workflow.set_entry_point("supervisor")

    workflow.add_edge("supervisor", "payroll_node")
    workflow.add_edge("payroll_node", END)

    return workflow.compile()

async def run_salary_agent(query: str, emp_id: str, session_id: str):
    graph = create_graph()
    initial_state = {
        "query": query, 
        "emp_id": emp_id, 
        "final_answer": "", 
        "next_node": ""
    }
    
    async for event in graph.astream(initial_state):
        for node_name, output in event.items():
            if "final_answer" in output:
                yield output["final_answer"]