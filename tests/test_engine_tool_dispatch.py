from core.engine import KaraEngine
from core.router import Intent
from core.tools import ToolResult


class DummyAssistant:
    def send_message(self, text: str) -> str:
        return "dummy"


class FakeTools:
    def __init__(self):
        self.executed = []

    def match_tool(self, text: str):
        return "get_time"

    def execute(self, name: str, **kwargs):
        self.executed.append(name)
        return ToolResult(success=True, message="mock time")


def test_engine_delegates_tool_selection_and_execution() -> None:
    tools = FakeTools()
    engine = KaraEngine(assistant=DummyAssistant(), tools=tools)

    resp = engine.process("What time is it?")

    assert resp.route.intent == Intent.TOOL
    assert resp.tool_result is not None
    assert resp.tool_result.success is True
    assert resp.tool_result.message == "mock time"
    assert tools.executed == ["get_time"]
