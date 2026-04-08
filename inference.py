"""
Inference script for the Code Review OpenEnv environment.

Uses an LLM (via OpenAI-compatible client) to review code snippets
and identify bugs, security issues, and best-practice violations.

Required env vars:
  API_BASE_URL  - LLM API endpoint
  MODEL_NAME    - Model identifier
  HF_TOKEN      - Hugging Face / API key
"""

import os
import sys
import json
import time
import uuid
import requests

from openai import OpenAI

# ── Config from environment ──────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/hf-inference/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-Coder-32B-Instruct")
HF_TOKEN = os.environ.get("HF_TOKEN")

ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:8000")

# ── OpenAI client (required by hackathon rules) ──────────────────
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call the LLM and return the response text."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1024,
    )
    return response.choices[0].message.content


SYSTEM_PROMPT = """You are an expert code reviewer. Given a code snippet and its context,
identify ALL bugs, security vulnerabilities, and best-practice violations.

Respond in this exact JSON format:
{
  "review": "Your detailed review text",
  "identified_issues": ["issue1", "issue2", ...],
  "severity_ratings": {"issue1": "critical", "issue2": "high", ...},
  "suggested_fixes": ["fix1", "fix2", ...]
}

Severity levels: critical, high, medium, low.
Be thorough. Check for: injection attacks, hardcoded secrets, race conditions,
missing error handling, input validation, authentication issues, etc."""


def env_reset() -> dict:
    """Reset the environment via HTTP."""
    resp = requests.post(f"{ENV_BASE_URL}/reset", json={})
    resp.raise_for_status()
    return resp.json()


def env_step(action: dict) -> dict:
    """Send a step to the environment via HTTP."""
    resp = requests.post(
        f"{ENV_BASE_URL}/step",
        json={"session_id": "default", "action": action},
    )
    resp.raise_for_status()
    return resp.json()


def run_task(task_obs: dict, task_num: int) -> dict:
    """Run a single task: send code to LLM, parse response, step env."""
    task_id = task_obs.get("task_id", "unknown")
    difficulty = task_obs.get("task_difficulty", "unknown")
    code = task_obs.get("code_snippet", "")
    language = task_obs.get("language", "")
    context = task_obs.get("context", "")
    issue_count = task_obs.get("known_issue_count", 0)

    user_prompt = f"""## Code Review Task
**Language:** {language}
**Context:** {context}
**Known issues to find:** {issue_count}

```{language}
{code}
```

Identify all bugs, security vulnerabilities, and best-practice violations."""

    # Call LLM
    raw_response = call_llm(SYSTEM_PROMPT, user_prompt)

    # Parse LLM response
    try:
        start = raw_response.find("{")
        end = raw_response.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(raw_response[start:end])
        else:
            parsed = {
                "review": raw_response,
                "identified_issues": [],
                "severity_ratings": {},
                "suggested_fixes": [],
            }
    except json.JSONDecodeError:
        parsed = {
            "review": raw_response,
            "identified_issues": [],
            "severity_ratings": {},
            "suggested_fixes": [],
        }

    action = {
        "review": parsed.get("review", raw_response),
        "identified_issues": parsed.get("identified_issues", []),
        "severity_ratings": parsed.get("severity_ratings", {}),
        "suggested_fixes": parsed.get("suggested_fixes", []),
    }

    # Step the environment
    result = env_step(action)
    score = result.get("reward", 0.0) or result.get("score", 0.0)

    # Emit [STEP] log
    print(
        f"[STEP] task_id={task_id} "
        f"difficulty={difficulty} "
        f"score={score} "
        f"issues_found={len(action['identified_issues'])} "
        f"step={task_num}"
    )

    return result


def main():
    """Main inference loop."""
    run_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    print(f"[START] run_id={run_id} model={MODEL_NAME} env={ENV_BASE_URL}")

    # Reset environment
    obs = env_reset()
    total_score = 0.0
    task_num = 0

    while not obs.get("done", False):
        task_num += 1
        obs = run_task(obs, task_num)
        score = obs.get("reward", 0.0) or obs.get("score", 0.0)
        total_score += score

    elapsed = time.time() - start_time
    avg_score = total_score / max(task_num, 1)

    print(
        f"[END] run_id={run_id} "
        f"tasks_completed={task_num} "
        f"total_score={total_score:.2f} "
        f"avg_score={avg_score:.2f} "
        f"elapsed_seconds={elapsed:.1f}"
    )


if __name__ == "__main__":
    main()
