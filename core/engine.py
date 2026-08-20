"""Kara orchestration engine.

Connects Kara's router, AI assistant, and approved tools.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.assistant import KaraAssistant
from core.router import Intent, KaraRouter, Route
from core.tools import KaraTools, ToolResult
from core.memory import Memory


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
        memory: Memory | None = None,
    ) -> None:
        self.assistant = assistant or KaraAssistant()
        self.router = router or KaraRouter()
        self.tools = tools or KaraTools()
        self.memory = memory

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
            return self._handle_memory_request(user_input, route)

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

    def _handle_memory_request(self, user_input: str, route: Route) -> EngineResponse:
        """Handle memory-related requests.

        Supports storing values with "remember key=value" and retrieving with
        "What is key?". If no memory backend is connected, preserve the
        previous behavior and return a message indicating memory isn't connected.
        """

        if self.memory is None:
            return EngineResponse(
                text=(
                    "Memory commands are recognized, "
                    "but the memory action layer is not connected yet."
                ),
                route=route,
            )

        text = user_input.strip()
        lowered = text.lower()

        # Handle store: remember key=value
        if lowered.startswith("remember "):
            # Extract the payload after the command
            payload = text[len("remember "):].strip()

            if "=" in payload:
                key, value = payload.split("=", 1)
                key = key.strip()
                value = value.strip()

                if key:
                    # Store in memory and confirm
                    self.memory.set(key, value)
                    return EngineResponse(
                        text=f"Stored '{key}' in memory.",
                        route=route,
                    )

            # If parsing failed, fall back to a helpful message
            return EngineResponse(
                text=(
                    "I couldn't understand that remember command. "
                    "Use: remember key=value"
                ),
                route=route,
            )

        # Handle retrieve: what is key?
        if lowered.startswith("what is "):
            # Extract the key portion and strip punctuation
            key = text[len("what is "):].strip().rstrip("? .!")

            if key:
                value = self.memory.get(key)

                if value is not None:
                    return EngineResponse(
                        text=str(value),
                        route=route,
                    )

                return EngineResponse(
                    text=f"I don't recall a value for '{key}'.",
                    route=route,
                )

        # Default fallback for other memory commands
        return EngineResponse(
            text=(
                "Memory command received but I couldn't process it. "
                "Try: remember key=value or What is key?"
            ),
            route=route,
        )
