import os
from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# Import your tools and calculator
from tools.document_tool import search_documents
from tools.database_tool import get_employee_info
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

async def supervisor(state: AgentState):
    """Decides which node should handle the user query."""
    prompt = (
        f"You are a helpful HR and Payroll assistant. Categorize this user request: '{state['query']}'.\n"
        "Respond with EXACTLY one of these labels:\n"
        "1. 'greeting_node' - If the user says Hi, Hello, or asks 'Who are you?'.\n"
        "2. 'payroll_node' - If they ask about salary, pay, calculations, or amounts.\n"
        "3. 'policy_node' - If they ask about company rules, leaves, or attendance.\n"
        "4. 'out_of_scope' - If the question is about food, weather, or anything unrelated to HR/Payroll."
    )
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    route = response.content.strip().lower()
    
    # Mapping logic to ensure exact node names
    if "greeting" in route:
        return {"next_node": "greeting_node"}
    elif "payroll" in route:
        return {"next_node": "payroll_node"}
    elif "policy" in route:
        return {"next_node": "policy_node"}
    else:
        return {"next_node": "out_of_scope"}

async def greeting_logic(state: AgentState):
    return {"final_answer": "Hello! I am your HR & Payroll assistant. How can I help you with your salary or policy queries today?"}

async def payroll_logic(state: AgentState):
    # Call the tool using .ainvoke()
    record = await get_employee_info.ainvoke({"emp_id": state["emp_id"]})
    
    if not record or "base" not in record:
        return {"final_answer": "I couldn't find your payroll records. Please contact HR."}

    result = calculate_prorated_salary(
        base_salary=record["base"], 
        total_days=record["total"], 
        present_days=record["present"]
    )
    
    return {"final_answer": f"Your calculated salary is {result['amount']} (Formula: {result['formula']})."}

async def policy_logic(state: AgentState):
    return {"final_answer": "Our policy states that prorated salary is calculated based on total calendar days in the month."}

async def out_of_scope_logic(state: AgentState):
    return {"final_answer": "I'm sorry, I am specifically trained to help with HR and Payroll questions. I can't assist with that request."}

# --- Graph Construction ---

def create_graph():
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("greeting_node", greeting_logic)
    workflow.add_node("payroll_node", payroll_logic)
    workflow.add_node("policy_node", policy_logic)
    workflow.add_node("out_of_scope", out_of_scope_logic)
    
    workflow.set_entry_point("supervisor")
    
    # Define routing
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_node"],
        {
            "greeting_node": "greeting_node",
            "payroll_node": "payroll_node",
            "policy_node": "policy_node",
            "out_of_scope": "out_of_scope"
        }
    )
    
    # All nodes lead to the end
    workflow.add_edge("greeting_node", END)
    workflow.add_edge("payroll_node", END)
    workflow.add_edge("policy_node", END)
    workflow.add_edge("out_of_scope", END)
    
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