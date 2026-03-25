import os
from typing import TypedDict, Annotated
import operator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import your tools and calculator
from tools.document_tool import search_documents
import re
from tools.database_tool import (
    get_employee_by_id,
    get_attendance,
    get_salary_payment,
    get_all_employees_data,
    admin_get_monthly_metrics,
    get_all_attendance_for_employee
)
from calculation.calculator import calculate_prorated_salary

# Initialize LLM with REST transport to avoid DNS/GRPC issues
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", 
    google_api_key=os.environ.get("GEMINI_API_KEY"),
)

llm.bind_tools([
    get_employee_by_id,
    get_attendance,
    get_salary_payment,
    get_all_employees_data,
    admin_get_monthly_metrics,
    get_all_attendance_for_employee
])

class AgentState(TypedDict):
    query: str
    emp_id: str
    final_answer: str
    next_node: str
    messages: Annotated[list, operator.add]

async def supervisor(state: AgentState):
    query = state["query"].lower()
    
    # Provide the router with the chat history so follow-ups ("And March?") map correctly
    recent_history = state.get("messages", [])[-4:]
    history_text = "\n".join([f"{type(m).__name__}: {m.content[:150]}" for m in recent_history])
    
    prompt = f"""
You are an intelligent HR Agent Router.
Analyze the user's query and categorize their intent into exactly ONE of the following categories:

- policy_node : Questions about company rules, HR policies, handbooks, time off, leave, or benefits.
- admin_node : Requests to view data, salaries, or records for ALL employees or everyone.
- payroll_node : Questions about the user's personal attendance, present/absent days, specific salary, personal payslips, deductions, or compensation.

Recent Conversation History:
{history_text}

User Query: "{query}"

You must respond with ONLY the exact category name. Do not include quotes or any other text.
"""
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    route = response.content.strip().strip('"').strip("'").lower()
    
    valid_routes = ["policy_node", "admin_node", "payroll_node"]
    if route in valid_routes:
        return {"next_node": route}
        
    # Fallback to defaults if the LLM hallucinates
    if state["emp_id"] == "ADMIN":
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

import re
from tools.database_tool import (
    get_employee_by_id,
    get_attendance,
    get_salary_payment
)
from calculation.calculator import calculate_prorated_salary
async def payroll_logic(state: AgentState):

    # Step 1: Employee
    employee = await get_employee_by_id.ainvoke({
        "emp_id": state["emp_id"]
    })

    if not employee or isinstance(employee, str):
        return {"final_answer": "I couldn't find your employee information. Please contact HR."}

    # Step 2: Extract month/year from query
    query = state["query"].lower()

    import json
    
    # 2. Intelligently extract the exact month/year the user is asking about
    date_prompt = f"""Extract the target month and year from this query.
Return ONLY a raw JSON dictionary. Do NOT use markdown code blocks.
If no month is explicitly or implicitly mentioned, set "month" to null.
If no year is mentioned, set "year" to null.
Example valid output: {{"month": 2, "year": 2026}}
here 1 is jan, 2 is feb, 3 is mar, 4 is apr, 5 is may, 6 is jun, 7 is jul, 8 is aug, 9 is sep, 10 is oct, 11 is nov, 12 is dec

Perform the exact payroll calculation. 
    Logic: Base * (Present / Total)
    amount = base_salary * (present_days / total_days)
    Suppose for an employee monthly salary = 30,000, but he was present for only 20 out of 30 days, The calculation can be shown as 30,000 * (20/30) = 20,000
Query: '{query}'
"""
    try:
        date_res = await llm.ainvoke([HumanMessage(content=date_prompt)])
        raw_json = date_res.content.strip().replace("```json", "").replace("```", "")
        extracted = json.loads(raw_json)
        extracted_month = extracted.get("month")
        extracted_year = extracted.get("year")
    except Exception:
        extracted_month = None
        extracted_year = None
        
    # --- Execute Business Target Rules ---
    current_demo_year = 2026
    
    if extracted_month is None and extracted_year is None:
        target_month = None
        target_year = current_demo_year
    elif extracted_month is None and extracted_year is not None:
        target_month = None
        target_year = extracted_year
    elif extracted_month is not None and extracted_year is None:
        target_month = extracted_month
        target_year = current_demo_year
    else:
        target_month = extracted_month
        target_year = extracted_year

    # --- Step 4: Format Data (MINIMAL CHANGE from your original logic) ---
    def format_data(data: dict, title: str):
        if not data:
            return f"{title}: Not available"
        return f"{title}:\n" + "\n".join([f"{k}: {v}" for k, v in data.items()])

    employee_data = format_data(employee, "Employee Data")

    # Fetch Data Based on Target Strategy
    if target_month is None:
        attendance_records = await get_all_attendance_for_employee.ainvoke({
            "emp_id": state["emp_id"],
            "year": target_year
        })
        
        if attendance_records:
            attendance_data = f"--- ATTENDANCE HISTORY ({target_year}) ---\n"
            
            # Extract baseline net pay for general salary inquiries
            base_net = employee.get('net_pay', 'N/A')
            salary_data = f"--- BASE SALARY ---\nFixed Net Salary: ₹{base_net} per month\n\n--- NET SALARY PAYOUTS ({target_year}) ---\n"
            
            for r in attendance_records:
                attendance_data += f"Month {r.get('month')}: Total Days: {r.get('total_days')}, Present: {r.get('present_days')}, Absent: {r.get('absent_days')}\n"
                
                # Fetch specific salary details for this month's attendance_id
                sal = await get_salary_payment.ainvoke({"attendance_id": r.get("attendance_id")})
                if sal and sal.get("final_salary"):
                    salary_data += f"Month {r.get('month')}: Paid Net: ₹{sal.get('final_salary')}\n"
                else:
                    salary_data += f"Month {r.get('month')}: Paid Net: Pending\n"
        else:
            attendance_data = f"Attendance Data: No records found for {target_year}"
            base_net = employee.get('net_pay', 'N/A')
            salary_data = f"Salary Data: Your fixed Net Salary is ₹{base_net} per month. No payouts recorded for {target_year}."
    else:
        attendance = await get_attendance.ainvoke({
            "emp_id": state["emp_id"],
            "month": target_month,
            "year": target_year
        })
        
        salary = None
        if attendance:
            salary = await get_salary_payment.ainvoke({
                "attendance_id": attendance["attendance_id"]
            })
            
        prorated_salary = None
        if not isinstance(employee, str) and attendance:
            try:
                base_sal = float(employee.get("basic_salary", 0))
                tot_days = int(attendance.get("total_days", 0))
                pres_days = int(attendance.get("present_days", 0))
                prorated_salary = calculate_prorated_salary(base_sal, tot_days, pres_days)
            except Exception as e:
                prorated_salary = {"error": f"Could not calculate: {str(e)}"}
# --- Step 4: Format Data (MINIMAL CHANGE from your original logic) ---
    def format_data(data, title: str):
        if not data:
            return f"{title}: Not available"
        if isinstance(data, list):
            # For list of records
            formatted = f"{title}:\n"
            for i, record in enumerate(data, 1):
                formatted += f"Record {i}:\n" + "\n".join([f"  {k}: {v}" for k, v in record.items()]) + "\n"
            return formatted
        else:
            # For single dict
            return f"{title}:\n" + "\n".join([f"{k}: {v}" for k, v in data.items()])

    prorated_data = ""
    if 'prorated_salary' in locals():
        prorated_data = format_data(prorated_salary, "Calculated Prorated Salary")
        
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

{prorated_data}

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

    past_messages = state.get("messages", [])
    response = await llm.ainvoke(past_messages + [HumanMessage(content=prompt)])

    return {
        "final_answer": response.content,
        "messages": [
            HumanMessage(content=state['query']),
            AIMessage(content=response.content)
        ]
    }
    # Extract values
    # basic = record["basic_salary"]
    # hra = record["hra"]
    # conveyance = record["conveyance"]
    # medical = record["medical"]
    # special = record["special"]

    # gross = record["gross_salary"]

    # epf = record["epf"]
    # insurance = record["health_insurance"]
    # tax = record["professional_tax"]
    # tds = record["tds"]

    # deductions = record["total_deductions"]
    # net = record["net_pay"]

    # return {
    #     "final_answer": (
    #         f"💼 Salary Breakdown:\n"
    #         f"Basic: ₹{basic}\n"
    #         f"HRA: ₹{hra}\n"
    #         f"Conveyance: ₹{conveyance}\n"
    #         f"Medical: ₹{medical}\n"
    #         f"Special Allowance: ₹{special}\n\n"
    #         f"📈 Gross Salary: ₹{gross}\n\n"
    #         f"📉 Deductions:\n"
    #         f"EPF: ₹{epf}\n"
    #         f"Health Insurance: ₹{insurance}\n"
    #         f"Professional Tax: ₹{tax}\n"
    #         f"TDS: ₹{tds}\n"
    #         f"Total Deductions: ₹{deductions}\n\n"
    #         f"💰 Net Pay: ₹{net}"
    #     )
    # }

async def admin_logic(state: AgentState):
    if state["emp_id"] != "ADMIN":
        return {"final_answer": "Unauthorized Access. Only the ADMIN can query data for all employees."}
    
    import json
    date_prompt = f"""Extract the target month and year from this admin query.
Return ONLY a raw JSON dictionary. Do NOT use markdown code blocks.
If no month is explicitly or implicitly mentioned, set "month" to null.
If no year is mentioned, set "year" to null.
Example valid output: {{"month": 2, "year": 2026}}

Query: '{state['query']}'
"""
    try:
        date_res = await llm.ainvoke([HumanMessage(content=date_prompt)])
        raw_json = date_res.content.strip().replace("```json", "").replace("```", "")
        extracted = json.loads(raw_json)
        extracted_month = extracted.get("month")
        extracted_year = extracted.get("year")
    except Exception:
        extracted_month = None
        extracted_year = None

    current_demo_year = 2026
    
    if extracted_month is None and extracted_year is None:
        target_month = None
        target_year = current_demo_year
    elif extracted_month is None and extracted_year is not None:
        target_month = None
        target_year = extracted_year
    elif extracted_month is not None and extracted_year is None:
        target_month = extracted_month
        target_year = current_demo_year
    else:
        target_month = extracted_month
        target_year = extracted_year

    base_records = await get_all_employees_data.ainvoke({})
    metrics = await admin_get_monthly_metrics.ainvoke({"month": target_month, "year": target_year})
    
    admin_data = "--- BASE EMPLOYEE DATA ---\n"
    admin_data += "\n".join([str(r) for r in base_records])
    
    if target_month is None:
        admin_data += f"\n\n--- AGGREGATE ATTENDANCE & SALARY DATA ({target_year}) ---\n"
    else:
        admin_data += f"\n\n--- MONTHLY ATTENDANCE & SALARY DATA (Month: {target_month}, Year: {target_year}) ---\n"
        
    admin_data += "\n".join([str(r) for r in metrics])

    prompt = f"""
You are an HR Admin Assistant.

Here is the data for ALL employees:
{admin_data}

Admin question:
{state['query']}

Instructions:
- Summarize or answer based on the dataset above.
- Be concise.
"""
    past_messages = state.get("messages", [])
    response = await llm.ainvoke(past_messages + [HumanMessage(content=prompt)])
    return {
        "final_answer": response.content,
        "messages": [
            HumanMessage(content=state['query']),
            AIMessage(content=response.content)
        ]
    }

# async def policy_logic(state: AgentState):
#     return {"final_answer": "Our policy states that prorated salary is calculated based on total calendar days in the month."}

# async def out_of_scope_logic(state: AgentState):
#     return {"final_answer": "I'm sorry, I am specifically trained to help with HR and Payroll questions. I can't assist with that request."}

async def policy_logic(state: AgentState):
    # Query your RAG database safely via synchronous python function call directly
    docs = search_documents.func(state["query"])
    
    prompt = f"""
You are an HR Policy Assistant. Use the following retrieved policy documents to answer the user's question.

Documents:
{docs}

Question:
{state['query']}

Instructions:
- Answer the user's question based strictly on the provided documents.
- If the documents don't contain the answer, politely state that you can't find it in the current policy handbook.
"""
    past_messages = state.get("messages", [])
    response = await llm.ainvoke(past_messages + [HumanMessage(content=prompt)])
    return {
        "final_answer": response.content,
        "messages": [
            HumanMessage(content=state['query']),
            AIMessage(content=response.content)
        ]
    }
# --- Graph Construction ---
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
            "policy_node": "policy_node"
        }
    )
    workflow.add_edge("payroll_node", END)
    workflow.add_edge("admin_node", END)
    workflow.add_edge("policy_node", END)

    return workflow.compile(checkpointer=memory)
 
async def run_salary_agent(query: str, emp_id: str, session_id: str):
    graph = create_graph()
    initial_state = {
        "query": query,
        "emp_id": emp_id,
        "final_answer": "",
        "next_node": "",
        "messages": []
    }
    config = {"configurable": {"thread_id": session_id}}

    async for event in graph.astream(initial_state, config):
        for node_name, output in event.items():
            if "final_answer" in output:
                yield output["final_answer"]