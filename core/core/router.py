"""Request router for Kara-Core.

The router classifies user requests into high-level intents.
It does not execute actions itself.

This keeps decision-making separate from tools and the AI assistant.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    """High-level request categories."""

    CHAT = "chat"
    MEMORY = "memory"
    TOOL = "tool"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Route:
    """Result returned by the router."""

    intent: Intent
    confidence: float
    reason: str


class KaraRouter:
    """Classifies requests before Kara decides what to do."""

    MEMORY_KEYWORDS = (
        "remember",
        "memorize",
        "don't forget",
        "do not forget",
        "forget this",
        "forget that",
        "what do you remember",
        "what you remember",
    )

    SYSTEM_KEYWORDS = (
        "shutdown",
        "restart",
        "turn off",
        "turn on",
        "system status",
        "system information",
    )

    TOOL_KEYWORDS = (
        "open",
        "launch",
        "run",
        "execute",
        "search",
        "download",
        "create a file",
        "delete a file",
        "move a file",
        "copy a file",
        "what time is it",
        "what's the time",
        "current time",
        "what date is it",
        "what's the date",
        "today's date",
    )

    def route(self, text: str) -> Route:
        """Classify a user request."""

        normalized = text.strip().lower()

        if not normalized:
            return Route(
                intent=Intent.UNKNOWN,
                confidence=1.0,
                reason="Empty request.",
            )

        if self._contains_any(normalized, self.MEMORY_KEYWORDS):
            return Route(
                intent=Intent.MEMORY,
                confidence=0.95,
                reason="Request contains memory-related language.",
            )

        if self._contains_any(normalized, self.SYSTEM_KEYWORDS):
            return Route(
                intent=Intent.SYSTEM,
                confidence=0.90,
                reason="Request appears to target the system.",
            )

        if self._contains_any(normalized, self.TOOL_KEYWORDS):
            return Route(
                intent=Intent.TOOL,
                confidence=0.80,
                reason="Request appears to require an external tool or action.",
            )

        return Route(
            intent=Intent.CHAT,
            confidence=0.70,
            reason="No special action was detected; treating request as conversation.",
        )

    @staticmethod
    def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
        """Return True when any keyword appears in the request."""

        return any(keyword in text for keyword in keywords)