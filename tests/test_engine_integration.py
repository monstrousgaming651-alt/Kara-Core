from core.engine import KaraEngine
from core.router import Intent


class DummyAssistant:
    def send_message(self, text: str) -> str:
        return "dummy response"


def test_time_request_runs_tool() -> None:
    engine = KaraEngine(assistant=DummyAssistant())

    resp = engine.process("What time is it?")

    assert resp.route.intent == Intent.TOOL
    assert resp.tool_result is not None
    assert resp.tool_result.success is True
    assert "time" in resp.tool_result.message.lower()


def test_date_request_runs_tool() -> None:
    engine = KaraEngine(assistant=DummyAssistant())

    resp = engine.process("What date is it?")

    assert resp.route.intent == Intent.TOOL
    assert resp.tool_result is not None
    assert resp.tool_result.success is True
    assert "today" in resp.tool_result.message.lower()
