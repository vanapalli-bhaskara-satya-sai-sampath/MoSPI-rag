import logging
from typing import Any

import ollama

from rag.config import OLLAMA_HOST, OLLAMA_MODEL, TEMPERATURE
from rag.prompt import build_prompt

logger = logging.getLogger(__name__)


def _normalize_model_names(models: Any) -> list[str]:
    names: list[str] = []

    if hasattr(models, "models"):
        raw_models = getattr(models, "models") or []
    elif isinstance(models, dict):
        raw_models = models.get("models", []) or []
    else:
        raw_models = models or []

    for item in raw_models:
        if hasattr(item, "model"):
            name = getattr(item, "model", "")
        elif isinstance(item, dict):
            name = item.get("name") or item.get("model") or ""
        elif isinstance(item, str):
            name = item
        else:
            name = ""

        if name:
            names.append(name)

    return sorted(set(names))


def extract_answer_text(response: Any) -> str:
    """Return only the assistant text from an Ollama chat response."""
    if isinstance(response, dict):
        message = response.get("message") or {}
    else:
        message = getattr(response, "message", None)

    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = getattr(message, "content", "")

    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(response, str):
        return response.strip()

    return "".join(str(part) for part in getattr(response, "message", []) if isinstance(part, str)).strip()


class OllamaClient:
    """Thin wrapper for Ollama chat calls."""

    def __init__(self, model: str = OLLAMA_MODEL, host: str = OLLAMA_HOST) -> None:
        self.model = model
        self.host = host
        self.client = ollama.Client(host=self.host)

    def generate(self, messages: list[dict[str, str]], temperature: float = TEMPERATURE, stream: bool = False) -> Any:
        logger.info("Ollama request host=%s model=%s temperature=%.2f stream=%s", self.host, self.model, temperature, stream)
        try:
            return self.client.chat(model=self.model, messages=messages, stream=stream, options={"temperature": temperature})
        except Exception as exc:
            logger.exception("Ollama request failed host=%s model=%s", self.host, self.model)
            raise RuntimeError(f"Unable to reach Ollama at {self.host} for model {self.model}.") from exc


def check_ollama_connection() -> dict[str, Any]:
    """Return detailed connectivity and model validation information for health checks."""
    host = OLLAMA_HOST
    model = OLLAMA_MODEL
    logger.info("Checking Ollama connectivity host=%s model=%s", host, model)

    try:
        client = ollama.Client(host=host)
        models = client.list()
        available = _normalize_model_names(models)
        model_found = model in available
        logger.info("Ollama reachable host=%s available_models=%s model_found=%s", host, available, model_found)
        return {
            "reachable": True,
            "model_found": model_found,
            "host": host,
            "model": model,
            "available_models": available,
            "reason": "Ollama reachable" if model_found else f"Model '{model}' not found in available models: {available}",
        }
    except Exception as exc:
        logger.exception("Ollama connectivity check failed host=%s model=%s", host, model)
        return {
            "reachable": False,
            "model_found": False,
            "host": host,
            "model": model,
            "available_models": [],
            "reason": str(exc),
        }


def generate_answer(question: str, context: str, temperature: float = TEMPERATURE, model: str | None = None) -> str:
    """Generate a grounded answer from retrieved context."""
    try:
        messages = build_prompt(question, context)
        logger.info("Ollama prompt question=%r context_length=%d", question, len(context))
        logger.info("Ollama context=%s", context)
        logger.info("Ollama messages=%s", messages)
        response = OllamaClient(model=model or OLLAMA_MODEL, host=OLLAMA_HOST).generate(messages, temperature=temperature, stream=False)
        answer = extract_answer_text(response)
        if answer:
            return answer
        return "I don't have that in my data."
    except Exception as exc:
        logger.exception("Answer generation failed for question=%r", question)
        raise RuntimeError("Unable to generate an answer from Ollama.") from exc
