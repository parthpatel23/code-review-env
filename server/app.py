"""FastAPI server for the Code Review environment."""

import json
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import CodeReviewAction
from server.environment import CodeReviewEnvironment

app = FastAPI(title="Code Review OpenEnv", version="1.0.0")

# Store per-session environments
_sessions: dict = {}


def _get_or_create_env(session_id: str) -> CodeReviewEnvironment:
    if session_id not in _sessions:
        _sessions[session_id] = CodeReviewEnvironment()
    return _sessions[session_id]


@app.get("/")
def root():
    return {
        "name": "Code Review OpenEnv",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": ["/health", "/reset", "/step", "/state", "/ws", "/docs"],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/reset")
def reset_env(body: dict = None):
    body = body or {}
    session_id = body.get("session_id", "default")
    env = _get_or_create_env(session_id)
    obs = env.reset(
        seed=body.get("seed"),
        episode_id=body.get("episode_id"),
    )
    return obs.model_dump()


@app.post("/step")
def step_env(body: dict):
    session_id = body.get("session_id", "default")
    env = _get_or_create_env(session_id)
    action = CodeReviewAction(**body.get("action", {}))
    obs = env.step(action)
    return obs.model_dump()


@app.get("/state")
def get_state(session_id: str = "default"):
    env = _get_or_create_env(session_id)
    return env.state.model_dump()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    env = _get_or_create_env(session_id)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            method = msg.get("method", "")

            if method == "reset":
                obs = env.reset(
                    seed=msg.get("seed"),
                    episode_id=msg.get("episode_id"),
                )
                await websocket.send_text(json.dumps(obs.model_dump()))

            elif method == "step":
                action = CodeReviewAction(**msg.get("action", {}))
                obs = env.step(action)
                await websocket.send_text(json.dumps(obs.model_dump()))

            elif method == "state":
                await websocket.send_text(json.dumps(env.state.model_dump()))

            else:
                await websocket.send_text(
                    json.dumps({"error": f"Unknown method: {method}"})
                )
    except WebSocketDisconnect:
        _sessions.pop(session_id, None)
