from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from core.engine import KaraEngine, EngineResponse
from core.router import Intent


class RouteModel(BaseModel):
    intent: str
    confidence: float
    reason: str


class EngineResponseModel(BaseModel):
    text: str
    route: RouteModel
    tool_result: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    text: str


def create_app(engine: KaraEngine) -> FastAPI:
    """Create a FastAPI app exposing a KaraEngine instance.

    The engine must be provided by the caller so tests can inject a dummy
    assistant and memory backend. This keeps the API layer separate from
    core engine logic.
    """

    app = FastAPI()
    app.state.engine = engine

    @app.get("/api/status")
    def status() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/tools")
    def tools() -> Dict[str, List[str]]:
        return {"tools": app.state.engine.tools.available()}

    @app.get("/api/memory")
    def memory() -> Dict[str, Any]:
        mem = app.state.engine.memory
        if mem is None:
            raise HTTPException(status_code=404, detail="Memory backend not connected")

        return {"memory": mem.all()}

    @app.post("/api/chat", response_model=EngineResponseModel)
    def chat(req: ChatRequest) -> EngineResponseModel:
        resp: EngineResponse = app.state.engine.process(req.text)

        route = RouteModel(
            intent=resp.route.intent.value if isinstance(resp.route.intent, Intent) else str(resp.route.intent),
            confidence=resp.route.confidence,
            reason=resp.route.reason,
        )

        tool_result = None
        if resp.tool_result is not None:
            # ToolResult is a dataclass with success and message
            tool_result = {"success": resp.tool_result.success, "message": resp.tool_result.message}

        return EngineResponseModel(text=resp.text, route=route, tool_result=tool_result)

    return app
