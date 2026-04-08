---
title: Code Review OpenEnv
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# Code Review OpenEnv Environment

An OpenEnv RL environment for training AI agents to perform code review. The agent reviews code snippets and identifies bugs, security vulnerabilities, and best-practice violations.

## Environment Description

The agent is presented with code snippets containing known issues. It must analyze the code and produce a structured review identifying:
- Security vulnerabilities (SQL injection, path traversal, JWT attacks, etc.)
- Bugs and logic errors (race conditions, missing error handling)
- Best-practice violations (hardcoded secrets, missing input validation)

## Action Space

| Field | Type | Description |
|-------|------|-------------|
| `review` | `str` | Detailed review text |
| `identified_issues` | `List[str]` | List of issues found |
| `severity_ratings` | `Dict[str, str]` | Issue → severity mapping |
| `suggested_fixes` | `List[str]` | Suggested code fixes |

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `str` | Current task identifier |
| `task_difficulty` | `str` | "easy", "medium", or "hard" |
| `code_snippet` | `str` | Code to review |
| `language` | `str` | Programming language |
| `context` | `str` | What the code should do |
| `known_issue_count` | `int` | Number of issues to find |
| `feedback` | `str` | Grader feedback |
| `score` | `float` | Score 0.0–1.0 |

## Tasks (3 difficulty tiers)

### Easy
- **SQL Injection** – Flask endpoint with string-concatenated SQL
- **Hardcoded Secrets** – SMTP script with plaintext credentials

### Medium
- **Race Condition** – Bank account class without thread safety
- **Path Traversal** – File server with unsanitized paths

### Hard
- **JWT Auth Flaws** – Authentication middleware with multiple vulnerabilities

## Reward Function

Keyword-matching grader that checks if the agent's review mentions expected issues. Each task has a set of expected issues with associated keywords. Score = (issues found) / (total issues). Returns 0.0–1.0 with partial credit.

## Setup

```bash
# Install dependencies
pip install -e .

# Or with uv
uv pip install -e .
```

## Run Locally

```bash
# Start the server
uvicorn server.app:app --host 0.0.0.0 --port 8000

# Run inference (in another terminal)
API_BASE_URL=https://api.openai.com/v1 MODEL_NAME=gpt-3.5-turbo HF_TOKEN=your-key python inference.py
```

## Deploy to Hugging Face Spaces

```bash
# Login to HF
huggingface-cli login

# Deploy
openenv push --repo-id your-username/code-review-env
```

## Docker

```bash
docker build -t code-review-env -f server/Dockerfile .
docker run -p 8000:8000 code-review-env
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `API_BASE_URL` | LLM API endpoint |
| `MODEL_NAME` | Model identifier for inference |
| `HF_TOKEN` | Hugging Face / API key |
