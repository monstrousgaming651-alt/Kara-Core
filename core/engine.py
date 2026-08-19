"""Kara orchestration engine.

Connects Kara's router, AI assistant, and approved tools.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.assistant import KaraAssistant
from core.router import Intent, KaraRouter, Route
from core.tools import KaraTools, ToolResult


@dataclass(frozen=True)
class EngineResponse:
    """Final response produced by the Kara engine."""

    text: str
    route: Route
    tool_result: ToolResult | None = None


class KaraEngine:
    """Central orchestration layer for Kara."""

    def __init__(
        self,
        assistant: KaraAssistant | None = None,
        router: KaraRouter | None = None,
        tools: KaraTools | None = None,
    ) -> None:
        self.assistant = assistant or KaraAssistant()
        self.router = router or KaraRouter()
        self.tools = tools or KaraTools()

    def process(self, user_input: str) -> EngineResponse:
        """Process one user request."""

        route = self.router.route(user_input)

        if route.intent == Intent.UNKNOWN:
            return EngineResponse(
                text="I didn't receive a request.",
                route=route,
            )

        if route.intent == Intent.CHAT:
            response = self.assistant.send_message(user_input)

            return EngineResponse(
                text=response,
                route=route,
            )

        if route.intent == Intent.TOOL:
            return self._handle_tool_request(user_input, route)

        if route.intent == Intent.MEMORY:
            return EngineResponse(
                text=(
                    "Memory commands are recognized, "
                    "but the memory action layer is not connected yet."
                ),
                route=route,
            )

        if route.intent == Intent.SYSTEM:
            return EngineResponse(
                text=(
                    "System actions are recognized, "
                    "but system-control tools are not enabled yet."
                ),
                route=route,
            )

        return EngineResponse(
            text="I couldn't determine how to handle that request.",
            route=route,
        )

    def _handle_tool_request(
        self,
        user_input: str,
        route: Route,
    ) -> EngineResponse:
        """Handle requests that may require a tool.

        Delegates tool selection to the KaraTools registry via match_tool(),
        then executes the selected tool using KaraTools.execute().
        """

        # Ask KaraTools which approved tool (if any) should handle this request.
        tool_name = self.tools.match_tool(user_input)

        if tool_name is not None:
            result = self.tools.execute(tool_name)

            return EngineResponse(
                text=result.message,
                route=route,
                tool_result=result,
            )

        # No matching approved tool found — preserve the existing fallback.
        return EngineResponse(
            text=(
                "I recognized that as a tool request, "
                "but I don't have an approved tool for it yet."
            ),
            route=route,
        )
