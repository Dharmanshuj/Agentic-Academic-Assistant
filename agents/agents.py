import os
from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# Import your tools and calculator
from tools.document_tool import search_documents
from tools.database_tool import get_employee_by_id, get_all_employees_data
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
async def payroll_logic(state: AgentState):
    record = await get_employee_by_id.ainvoke({
        "emp_id": state["emp_id"]
    })

    if not record or isinstance(record, str):
        return {"final_answer": "I couldn't find your employee information. Please contact HR."}

    employee_data = "\n".join([f"{k}: {v}" for k, v in record.items()])

    prompt = f"""
You are an intelligent HR and Payroll assistant.

Here is the employee's salary data:
{employee_data}

User question:
{state['query']}

Instructions:
- Answer ONLY based on the given data
- If user asks meaning (like EPF, TDS), explain clearly
- If user asks salary → give correct numbers
- Be concise and professional
"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {"final_answer": response.content}
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
    
    records = await get_all_employees_data.ainvoke({})
    
    admin_data = "\n".join([str(r) for r in records])
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
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"final_answer": response.content}

# async def policy_logic(state: AgentState):
#     return {"final_answer": "Our policy states that prorated salary is calculated based on total calendar days in the month."}

# async def out_of_scope_logic(state: AgentState):
#     return {"final_answer": "I'm sorry, I am specifically trained to help with HR and Payroll questions. I can't assist with that request."}

# --- Graph Construction ---
def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor)
    workflow.add_node("payroll_node", payroll_logic)
    workflow.add_node("admin_node", admin_logic)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_node"],
        {
            "payroll_node": "payroll_node",
            "admin_node": "admin_node"
        }
    )
    workflow.add_edge("payroll_node", END)
    workflow.add_edge("admin_node", END)

    return workflow.compile()
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