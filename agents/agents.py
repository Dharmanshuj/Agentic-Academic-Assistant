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

async def supervisor(state: AgentState):
    query = state["query"].lower()
    
    prompt = f"""
You are an intelligent HR Agent Router.
Analyze the user's query and categorize their intent into exactly ONE of the following categories:

- policy_node : Questions about company rules, HR policies, handbooks, time off, leave, or benefits.
- admin_node : Requests to view data, salaries, or records for ALL employees or everyone.
- payroll_node : Questions about the user's own specific salary, personal payslips, deductions, or compensation.

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
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"final_answer": response.content}

# --- Graph Construction ---
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

    return workflow.compile()

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