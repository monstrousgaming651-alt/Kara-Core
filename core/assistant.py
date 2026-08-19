"""Core assistant implementation for Kara-Core."""

from __future__ import annotations

import os
from typing import Optional


try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class MissingAPIKeyError(RuntimeError):
    """Raised when OPENAI_API_KEY is not configured."""


class KaraAssistant:
    """Kara's primary AI interface."""

    DEFAULT_MODEL = "gpt-5.6"

    SYSTEM_PROMPT = """
You are Kara.

You are a professional, intelligent personal AI assistant.
You are warm, confident, concise, and highly capable.

Your purpose is to help your user understand information,
solve problems, plan tasks, and eventually control connected
tools and systems.

Do not claim to have performed an action unless the system
actually performed it.

When tools become available, use them deliberately and safely.

For normal conversation, respond naturally and clearly.
""".strip()

    def __init__(self, model: Optional[str] = None) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise MissingAPIKeyError(
                "OPENAI_API_KEY is not configured."
            )

        if OpenAI is None:
            raise RuntimeError(
                "OpenAI SDK is not installed. Run: pip install openai"
            )

        self.model = (
            model
            or os.environ.get("KARA_MODEL")
            or self.DEFAULT_MODEL
        )

        self.client = OpenAI(api_key=api_key)

        self.history: list[dict[str, str]] = []

    def reset(self) -> None:
        """Clear Kara's current conversation."""
        self.history.clear()

    def send_message(self, text: str) -> str:
        """Send a message to Kara and return her response."""

        if not text.strip():
            return ""

        response = self.client.responses.create(
            model=self.model,
            instructions=self.SYSTEM_PROMPT,
            input=self.history + [
                {
                    "role": "user",
                    "content": text,
                }
            ],
        )

        reply = response.output_text

        self.history.append(
            {
                "role": "user",
                "content": text,
            }
        )

        self.history.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        return reply