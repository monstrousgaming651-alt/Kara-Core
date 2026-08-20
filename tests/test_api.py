from fastapi.testclient import TestClient
from core.memory import Memory
from core.router import Intent
from core.engine import KaraEngine

from interface.api import create_app


class DummyAssistant:
    def send_message(self, text: str) -> str:
        return "dummy response"


def test_status_endpoint():
    engine = KaraEngine(assistant=DummyAssistant(), memory=None)
    app = create_app(engine)
    client = TestClient(app)

    resp = client.get("/api/status")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_tools_endpoint():
    engine = KaraEngine(assistant=DummyAssistant(), memory=None)
    app = create_app(engine)
    client = TestClient(app)

    resp = client.get("/api/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
    assert "get_time" in data["tools"]


def test_memory_endpoints_and_chat(tmp_path):
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    app = create_app(engine)
    client = TestClient(app)

    # Initially empty
    resp = client.get("/api/memory")
    assert resp.status_code == 200
    assert resp.json() == {"memory": {}}

    # Store via chat
    resp = client.post("/api/chat", json={"text": "remember favorite_color=blue"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["route"]["intent"] == "memory"
    assert "stored" in data["text"].lower()
    assert "favorite_color" in data["text"]
    assert mem.get("favorite_color") == "blue"

    # Retrieve via chat
    resp = client.post("/api/chat", json={"text": "What is favorite_color?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["route"]["intent"] == "memory"
    assert "blue" in data["text"]
