import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rag.config import TEMPERATURE, TOP_K
from rag.ingest import rebuild_index
from rag.llm import check_ollama_connection, generate_answer
from rag.retriever import Retriever
from rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)

app = FastAPI(title="MoSPI RAG Chatbot")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class AskResponse(BaseModel):
    answer: str
    citations: list[dict[str, str]]


@app.get("/health")
def health() -> dict[str, Any]:
    status = check_ollama_connection()
    return {
        "status": "healthy" if status.get("reachable") else "degraded",
        "ollama": "available" if status.get("reachable") and status.get("model_found") else "unavailable",
        "host": status.get("host"),
        "model": status.get("model"),
        "model_found": status.get("model_found"),
        "reason": status.get("reason"),
    }


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    try:
        vector_store = VectorStore()
        retriever = Retriever(vector_store)
        chunks = retriever.retrieve(payload.question, top_k=TOP_K)
        if not chunks:
            logger.info("No chunks retrieved for question=%s", payload.question)
            return AskResponse(answer="I don't have that in my data.", citations=[])

        context = "\n\n".join(chunk["text"] for chunk in chunks if chunk.get("text"))
        answer = generate_answer(payload.question, context, temperature=TEMPERATURE)

        citations = [
            {"title": chunk.get("title", "Untitled"), "url": chunk.get("url", "")}
            for chunk in chunks
            if chunk.get("title") or chunk.get("url")
        ]
        logger.info("Answered question=%s with %d citation(s)", payload.question, len(citations))
        return AskResponse(answer=answer, citations=citations)
    except Exception as exc:
        logger.exception("Ask endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ingest")
def ingest() -> dict[str, str]:
    try:
        result = rebuild_index()
        return {"status": "success" if result.get("status") == "success" else "error"}
    except Exception as exc:
        logger.exception("Ingest endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
