from core.engine import KaraEngine
from core.memory import Memory
from core.router import Intent


class DummyAssistant:
    def send_message(self, text: str) -> str:
        return "dummy response"


def test_store_memory_through_engine(tmp_path) -> None:
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)

    resp = engine.process("remember favorite_color=blue")

    assert resp.route.intent == Intent.MEMORY
    assert mem.get("favorite_color") == "blue"
    assert "stored" in resp.text.lower()
    assert "favorite_color" in resp.text


def test_retrieve_memory_through_engine(tmp_path) -> None:
    mem = Memory(path=str(tmp_path / "mem.json"))
    mem.set("favorite_color", "blue")
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)

    resp = engine.process("What is favorite_color?")

    assert resp.route.intent == Intent.MEMORY
    assert "blue" in resp.text