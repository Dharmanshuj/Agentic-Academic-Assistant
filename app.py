from fastapi import FastAPI
from api.chat_routes import router

app = FastAPI(
    title="AI Payroll Chatbot"
)

app.include_router(router)