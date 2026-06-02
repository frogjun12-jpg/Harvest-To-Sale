import os

import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")

client = ollama.Client(host=OLLAMA_BASE_URL)


def embed_text(text: str) -> list[float]:
    response = client.embeddings(model=EMBEDDING_MODEL, prompt=text)
    return response["embedding"]
