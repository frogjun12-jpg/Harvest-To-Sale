import os

import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:7b")

client = ollama.Client(host=OLLAMA_BASE_URL)


def generate_answer(prompt: str) -> str:
    response = client.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful Korean RAG assistant."},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.2},
    )
    return response["message"]["content"]
