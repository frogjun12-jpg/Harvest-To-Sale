import os

import ollama
from openai import OpenAI

from app.config import load_app_env

load_app_env()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").strip().lower()
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

client = ollama.Client(host=OLLAMA_BASE_URL)


def embed_text(text: str) -> list[float]:
    if EMBEDDING_PROVIDER == "openai":
        openai_base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        if not openai_base_url:
            os.environ.pop("OPENAI_BASE_URL", None)

        client_options = {"api_key": os.getenv("OPENAI_API_KEY")}
        if openai_base_url:
            client_options["base_url"] = openai_base_url

        response = OpenAI(**client_options).embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    response = client.embeddings(model=EMBEDDING_MODEL, prompt=text)
    return response["embedding"]
