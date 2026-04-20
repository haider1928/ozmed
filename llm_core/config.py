import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

GROQ_API_KEY = os.getenv("GROQ_API_KEY1")
#print("KEY LOADED:", GROQ_API_KEY)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = open("llm_core/system_prompt.txt", 'r', encoding='utf-8').read()