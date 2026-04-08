"""Client for the Code Review environment."""

import json
import requests
from typing import Optional
from models import (
    CodeReviewAction,
    CodeReviewObservation,
    CodeReviewState,
)


class CodeReviewEnv:
    """HTTP client for the Code Review OpenEnv environment."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session_id = None

    def reset(self, seed=None, episode_id=None) -> CodeReviewObservation:
        body = {}
        if seed is not None:
            body["seed"] = seed
        if episode_id is not None:
            body["episode_id"] = episode_id

        resp = requests.post(f"{self.base_url}/reset", json=body)
        resp.raise_for_status()
        data = resp.json()
        self.session_id = data.get("metadata", {}).get("session_id")
        return CodeReviewObservation(**data)

    def step(self, action: CodeReviewAction) -> CodeReviewObservation:
        body = {
            "session_id": self.session_id or "default",
            "action": action.model_dump(),
        }
        resp = requests.post(f"{self.base_url}/step", json=body)
        resp.raise_for_status()
        return CodeReviewObservation(**resp.json())

    def state(self) -> CodeReviewState:
        params = {}
        if self.session_id:
            params["session_id"] = self.session_id
        resp = requests.get(f"{self.base_url}/state", params=params)
        resp.raise_for_status()
        return CodeReviewState(**resp.json())

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()
