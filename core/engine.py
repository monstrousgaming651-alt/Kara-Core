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
        # Preserve backward compatibility: create Memory if not provided
        self.memory = memory or Memory()

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
        """Handle simple memory commands.

        Supported syntaxes (minimal and deterministic):
        - "remember key=value"  -> stores value under key
        - "what is key" or "what is key?" -> retrieves value for key
        - "what do you remember" -> lists all memories
        """

        normalized = user_input.strip()
        lower = normalized.lower()

        # Store: remember key=value
        if lower.startswith("remember "):
            body = normalized[len("remember "):].strip()
            if "=" in body:
                key, value = body.split("=", 1)
                key = key.strip()
                value = value.strip()
                try:
                    self.memory.set(key, value)
                    return EngineResponse(
                        text=f"Stored memory '{key}'.",
                        route=route,
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    return EngineResponse(
                        text=f"Failed to store memory: {exc}",
                        route=route,
                    )

        # Retrieve: what is key?
        if lower.startswith("what is "):
            key = lower[len("what is "):].strip()
            if key.endswith("?"):
                key = key[:-1].strip()
            value = self.memory.get(key)
            if value is not None:
                return EngineResponse(
                    text=str(value),
                    route=route,
                )
            return EngineResponse(
                text=f"I don't have a memory for '{key}'.",
                route=route,
            )

        # List all memories
        if lower.startswith("what do you remember"):
            all_mem = self.memory.all()
            return EngineResponse(
                text=str(all_mem),
                route=route,
            )

        # Fallback: preserve existing message
        return EngineResponse(
            text=(
                "Memory commands are recognized, "
                "but the memory action layer is not connected yet."
            ),
            route=route,
        )
