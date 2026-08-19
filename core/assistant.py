"""Core assistant implementation for Kara-Core v0.1.

Uses the official OpenAI Python SDK (Responses API) to send/receive messages.
Conversation state is kept in-memory for the running process. No persistent
memory is implemented in this version.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os

try:
    # Official OpenAI Python SDK (newer versions expose OpenAI client)
    from openai import OpenAI
except Exception:  # pragma: no cover - tests will mock out OpenAI import as needed
    OpenAI = None  # type: ignore


class MissingAPIKeyError(RuntimeError):
    """Raised when OPENAI_API_KEY is not set in the environment."""


@dataclass
class Message:
    role: str
    content: str


class KaraAssistant:
    """A small wrapper around the OpenAI Responses API for multi-turn chat.

    Usage:
        assistant = KaraAssistant()
        reply = assistant.send_message("Hello")
        assistant.reset()

    The assistant requires OPENAI_API_KEY to be set in the environment. The
    model may be provided with the KARA_MODEL environment variable; otherwise
    the default 'gpt-5.6' is used.
    """

    DEFAULT_MODEL = "gpt-5.6"

    def __init__(self, model: Optional[str] = None) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise MissingAPIKeyError(
                "OPENAI_API_KEY not set in environment. Please set it before running Kara."
            )

        self.model = model or os.environ.get("KARA_MODEL") or self.DEFAULT_MODEL

        if OpenAI is None:  # pragma: no cover - runtime import guard
            raise RuntimeError("OpenAI SDK not available. Install the 'openai' package.")

        # Create a client instance. The OpenAI client expects the API key to be
        # provided either via the environment or explicitly passed.
        # We prefer environment-based auth but pass it explicitly for clarity.
        self._client = OpenAI(api_key=api_key)

        # Conversation messages: start with a system message to set personality.
        self._system_prompt = (
            "You are Kara, a professional, warm, and highly capable assistant. "
            "Answer concisely and helpfully. Maintain a polite, professional tone."
        )
        self._messages: List[Dict[str, str]] = [
            {"role": "system", "content": self._system_prompt}
        ]

    def reset(self) -> None:
        """Reset conversation state except for the system/developer instructions.

        After reset, only the system message remains in the internal message list.
        """
        self._messages = [{"role": "system", "content": self._system_prompt}]

    def send_message(self, text: str, max_tokens: Optional[int] = None) -> str:
        """Send a user message to the model and return the assistant reply.

        This method appends the user message to the in-memory history, calls the
        Responses API, appends the assistant reply to the history, and returns
        the assistant text. API errors are propagated to the caller.
        """
        if not text:
            return ""

        user_entry = {"role": "user", "content": text}
        self._messages.append(user_entry)

        # Prepare request parameters.
        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": self._messages,
        }
        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        # Call the Responses API. Tests should mock this call.
        try:
            response = self._client.responses.create(**request_kwargs)
        except Exception:
            # Roll back user message on failure to keep internal state consistent.
            # (We could also choose to keep it, but for clarity revert.)
            self._messages.pop()
            raise

        # Parse assistant reply. The Responses API may return different shapes
        # depending on the SDK version; attempt a few reasonable access patterns.
        assistant_text = self._parse_response(response)

        # Append assistant reply to conversation history if present.
        if assistant_text:
            self._messages.append({"role": "assistant", "content": assistant_text})

        return assistant_text

    @staticmethod
    def _parse_response(response: Any) -> str:
        """Extract assistant text from a Responses API response object.

        The SDK's response shape can vary; try a few common access patterns and
        fall back to a string representation if needed.
        """
        # Preferred: response.output[0].content[0].text or .content[0]['text']
        try:
            out = getattr(response, "output", None)
            if out:
                # out may be a list of content blocks
                parts: List[str] = []
                for item in out:
                    # item may contain 'content' which is a list
                    content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
                    if isinstance(content, list):
                        for c in content:
                            # c may be dict with 'text' or 'type' fields
                            if isinstance(c, dict):
                                text = c.get("text") or c.get("content")
                                if text:
                                    parts.append(str(text))
                            else:
                                parts.append(str(c))
                    elif isinstance(content, str):
                        parts.append(content)
                if parts:
                    return "\n".join(parts)
        except Exception:
            pass

        # Older SDKs may return 'choices' with 'message' content.
        try:
            choices = getattr(response, "choices", None)
            if choices:
                parts = []
                for ch in choices:
                    msg = ch.get("message") if isinstance(ch, dict) else getattr(ch, "message", None)
                    if msg:
                        if isinstance(msg, dict):
                            txt = msg.get("content")
                            if txt:
                                parts.append(str(txt))
                        else:
                            # msg might be an object with content attribute
                            content = getattr(msg, "content", None)
                            if isinstance(content, str):
                                parts.append(content)
                if parts:
                    return "\n".join(parts)
        except Exception:
            pass

        # Fallback: try to convert the whole response to string.
        try:
            return str(response)
        except Exception:
            return ""

    @property
    def history(self) -> List[Dict[str, str]]:
        """Return a shallow copy of the current conversation history."""
        return list(self._messages)
