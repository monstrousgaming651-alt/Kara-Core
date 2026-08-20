"""Safe tool layer for Kara-Core.

Tools are deliberately small and controlled.
The router decides what kind of request was made;
this module defines what Kara is actually allowed to do.
"""

from __future__ import annotations

import re
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
            "calculate": self.calculate,
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

        # Check for calculator keywords
        if any(
            keyword in normalized
            for keyword in ("calculate", "compute", "what is", "equals", "math")
        ):
            return "calculate"

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

    @staticmethod
    def calculate(expression: str = "") -> ToolResult:
        """Safely evaluate a mathematical expression.

        Supports:
        - Basic arithmetic: +, -, *, /, %
        - Parentheses for grouping
        - Decimal numbers
        - Whitespace (ignored)

        Rejects:
        - Function calls (sin, sqrt, etc.)
        - Variables or identifiers
        - Dangerous operators (**, //, &, |, ^, ~, etc.)
        - Any non-math characters

        Args:
            expression: The math expression to evaluate.

        Returns:
            ToolResult with success=True and the computed result,
            or success=False with an error message.
        """

        if not expression or not isinstance(expression, str):
            return ToolResult(
                success=False,
                message="No expression provided.",
            )

        expr_stripped = expression.strip()

        if not expr_stripped:
            return ToolResult(
                success=False,
                message="No expression provided.",
            )

        # Remove all whitespace
        expr_clean = "".join(expr_stripped.split())

        # Whitelist allowed characters:
        # - Digits: 0-9
        # - Decimal point: .
        # - Operators: + - * / %
        # - Parentheses: ( )
        if not re.match(r"^[0-9.+\-*/%() ]*$", expr_clean):
            return ToolResult(
                success=False,
                message=f"Invalid characters in expression: {expr_stripped}",
            )

        # Reject consecutive operators or invalid patterns
        # e.g. "5++3", "5*", "()", "5.-3", etc.
        if re.search(r"[+\-*/%]{2,}", expr_clean):
            return ToolResult(
                success=False,
                message=f"Invalid operator sequence: {expr_stripped}",
            )

        # Reject standalone parentheses
        if re.search(r"\(\s*\)", expr_clean):
            return ToolResult(
                success=False,
                message=f"Empty parentheses: {expr_stripped}",
            )

        # Reject numbers starting with multiple decimal points
        if re.search(r"\d+\.\d+\.", expr_clean):
            return ToolResult(
                success=False,
                message=f"Invalid decimal number: {expr_stripped}",
            )

        # Reject leading/trailing operators
        if re.match(r"^[+\-*/%]", expr_clean) or re.search(r"[+\-*/%]$", expr_clean):
            return ToolResult(
                success=False,
                message=f"Expression starts or ends with an operator: {expr_stripped}",
            )

        # Check for balanced parentheses
        paren_count = 0
        for char in expr_clean:
            if char == "(":
                paren_count += 1
            elif char == ")":
                paren_count -= 1
            if paren_count < 0:
                return ToolResult(
                    success=False,
                    message=f"Unbalanced parentheses: {expr_stripped}",
                )

        if paren_count != 0:
            return ToolResult(
                success=False,
                message=f"Unbalanced parentheses: {expr_stripped}",
            )

        # Safely evaluate using Python's eval with a restricted namespace
        try:
            # Use a restricted context with only built-in math operations
            result = eval(expr_clean, {"__builtins__": {}}, {})

            # Ensure result is a number
            if not isinstance(result, (int, float)):
                return ToolResult(
                    success=False,
                    message=f"Expression did not return a number: {expr_stripped}",
                )

            # Format the result nicely
            if isinstance(result, float) and result.is_integer():
                result_str = str(int(result))
            else:
                result_str = str(result)

            return ToolResult(
                success=True,
                message=f"{expr_stripped} = {result_str}",
            )

        except ZeroDivisionError:
            return ToolResult(
                success=False,
                message=f"Division by zero: {expr_stripped}",
            )
        except ValueError as exc:
            return ToolResult(
                success=False,
                message=f"Invalid expression: {expr_stripped} ({exc})",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                message=f"Calculation failed: {exc}",
            )
