"""Minimal local Ollama chat client.

Talks to a locally-running Ollama server (http://localhost:11434 by
default) — no API key involved, since Ollama itself doesn't require
auth for local use. Kept dependency-light (just `requests`) and
synchronous; the chat window runs calls in a QThread so the UI doesn't
block (see features/chat_window.py).
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"
REQUEST_TIMEOUT_SECONDS = 60


class OllamaError(RuntimeError):
    pass


class OllamaUnavailableError(OllamaError):
    """Raised when the local Ollama server can't be reached at all."""


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant" | "system"
    content: str


class OllamaClient:
    def __init__(self, host: str = DEFAULT_HOST, model: str = DEFAULT_MODEL) -> None:
        self.host = host.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=3)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> list[str]:
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except requests.RequestException as exc:
            raise OllamaUnavailableError(
                f"Could not reach Ollama at {self.host}: {exc}"
            ) from exc

    def chat(
        self,
        history: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> str:
        """Send the full conversation and return the assistant's reply text."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend({"role": m.role, "content": m.content} for m in history)

        try:
            resp = requests.post(
                f"{self.host}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
        except requests.ConnectionError as exc:
            raise OllamaUnavailableError(
                f"Ollama isn't reachable at {self.host}. Is `ollama serve` running?"
            ) from exc
        except requests.RequestException as exc:
            raise OllamaError(f"Ollama request failed: {exc}") from exc

        data = resp.json()
        message = data.get("message", {})
        content = message.get("content")
        if not content:
            raise OllamaError("Ollama returned an empty response.")
        return content

DEFAULT_PET_SYSTEM_PROMPT = (
    "You are a small, friendly desktop pet living on the user's screen. "
    "Keep replies short (1-3 sentences), warm, and a little playful, "
    "like a companion rather than a generic assistant."
)
