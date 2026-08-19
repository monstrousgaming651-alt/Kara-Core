"""Tests for Kara Core routing and tools."""

from core.router import Intent, KaraRouter
from core.tools import KaraTools


def test_chat_request_is_routed_to_chat() -> None:
    router = KaraRouter()

    result = router.route("Explain black holes to me.")

    assert result.intent == Intent.CHAT
    assert result.confidence > 0


def test_memory_request_is_routed_to_memory() -> None:
    router = KaraRouter()

    result = router.route("Remember that I like cappuccino.")

    assert result.intent == Intent.MEMORY


def test_tool_request_is_routed_to_tool() -> None:
    router = KaraRouter()

    result = router.route("What time is it?")

    assert result.intent == Intent.TOOL


def test_system_request_is_routed_to_system() -> None:
    router = KaraRouter()

    result = router.route("Restart the computer.")

    assert result.intent == Intent.SYSTEM


def test_empty_request_is_unknown() -> None:
    router = KaraRouter()

    result = router.route("")

    assert result.intent == Intent.UNKNOWN


def test_time_tool_is_available() -> None:
    tools = KaraTools()

    assert "get_time" in tools.available()


def test_date_tool_is_available() -> None:
    tools = KaraTools()

    assert "get_date" in tools.available()


def test_time_tool_executes_successfully() -> None:
    tools = KaraTools()

    result = tools.execute("get_time")

    assert result.success is True
    assert "current time" in result.message.lower()


def test_date_tool_executes_successfully() -> None:
    tools = KaraTools()

    result = tools.execute("get_date")

    assert result.success is True
    assert "today" in result.message.lower()


def test_unknown_tool_is_rejected() -> None:
    tools = KaraTools()

    result = tools.execute("delete_everything")

    assert result.success is False