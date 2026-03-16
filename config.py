import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def get_llm():

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key="AIzaSyCXI59XKDTY_ZmajdHfjG53KdTTNqgcE1I",
        temperature=0
    )