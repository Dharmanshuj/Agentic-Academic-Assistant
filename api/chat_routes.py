from fastapi import APIRouter
from agents.agents import chatbot_agent

router = APIRouter()

@router.get("/chat")
def chat(query: str):

    result = chatbot_agent.invoke({
        "messages": [("user", query)]
    })

    return {
        "response": result["messages"][-1].content
    }