"""Safe tool layer for Kara-Core.

Tools are deliberately small and controlled.
The router decides what kind of request was made;
this module defines what Kara is actually allowed to do.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass(frozen=True)
class ToolResult:
    """Result returned by a tool."""

    success: bool
    message: str


class KaraTools:
    """Registry and executor for Kara's approved tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., ToolResult]] = {
            "get_time": self.get_time,
            "get_date": self.get_date,
        }

    def available(self) -> list[str]:
        """Return the names of available tools."""

        return sorted(self._tools.keys())

    def execute(self, name: str, **kwargs: object) -> ToolResult:
        """Execute an approved tool by name."""

        tool = self._tools.get(name)

        if tool is None:
            return ToolResult(
                success=False,
                message=f"Tool '{name}' is not available.",
            )

        try:
            return tool(**kwargs)
        except Exception as exc:
            return ToolResult(
                success=False,
                message=f"Tool '{name}' failed: {exc}",
            )

    def match_tool(self, text: str) -> str | None:
        """Return the approved tool name for a given request text, or None.

        This keeps the mapping/heuristics for selecting a tool centralized
        in the KaraTools registry so KaraEngine doesn't need tool-specific
        branching logic.
        """

        normalized = text.strip().lower()

        # Mirror the same heuristics used previously in KaraEngine.
        if "time" in normalized:
            return "get_time"

        if "date" in normalized or "today" in normalized:
            return "get_date"

        return None

    @staticmethod
    def get_time() -> ToolResult:
        """Return the current local time."""

        current_time = datetime.now().strftime("%I:%M %p")

        return ToolResult(
            success=True,
            message=f"The current time is {current_time}.",
        )

    @staticmethod
    def get_date() -> ToolResult:
        """Return the current local date."""

        current_date = datetime.now().strftime("%A, %d %B %Y")

        return ToolResult(
            success=True,
            message=f"Today is {current_date}.",
        )
