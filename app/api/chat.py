from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.llm.ollama_client import generate_answer
from app.rag.prompt_builder import build_prompt
from app.rag.retriever import retrieve_context

router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


class SourceChunk(BaseModel):
    source_path: str
    chunk_index: int
    content: str
    distance: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        chunks = retrieve_context(request.question)
        prompt = build_prompt(request.question, chunks)
        answer = generate_answer(prompt)
        return ChatResponse(answer=answer, sources=[SourceChunk(**chunk) for chunk in chunks])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
