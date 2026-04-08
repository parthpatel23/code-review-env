"""Task definitions for the Code Review environment.

Each task has:
- A code snippet with known issues
- Expected issues the agent should find
- A grader function that scores the agent's review
"""

from typing import List, Dict, Callable
from dataclasses import dataclass, field


@dataclass
class ReviewTask:
    task_id: str
    difficulty: str  # "easy", "medium", "hard"
    language: str
    context: str
    code_snippet: str
    expected_issues: List[str]
    issue_severities: Dict[str, str]
    grader: Callable  # function(identified_issues, review_text) -> float


def _keyword_match_score(identified: List[str], review: str, expected: List[str]) -> float:
    """Score based on how many expected issues were found. Returns 0.0-1.0."""
    if not expected:
        return 1.0
    review_lower = review.lower()
    combined = " ".join(identified).lower() + " " + review_lower
    found = 0
    for issue_keywords in expected:
        # Each expected issue is a comma-separated list of keywords (any match counts)
        keywords = [k.strip().lower() for k in issue_keywords.split(",")]
        if any(kw in combined for kw in keywords):
            found += 1
    return round(found / len(expected), 2)


# ============================================================
# EASY TASKS
# ============================================================

TASK_EASY_1 = ReviewTask(
    task_id="easy_sql_injection",
    difficulty="easy",
    language="python",
    context="A Flask web endpoint that queries a user database by username.",
    code_snippet='''from flask import Flask, request
import sqlite3

app = Flask(__name__)

@app.route("/user")
def get_user():
    username = request.args.get("username")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return {"user": result}
''',
    expected_issues=[
        "sql injection, string concatenation, unsanitized input",
        "no input validation, missing validation",
        "connection not closed on error, no error handling, no try",
    ],
    issue_severities={
        "SQL Injection": "critical",
        "No input validation": "high",
        "No error handling": "medium",
    },
    grader=lambda ids, review: _keyword_match_score(ids, review, [
        "sql injection, string concatenation, unsanitized input",
        "no input validation, missing validation",
        "connection not closed on error, no error handling, no try",
    ]),
)

TASK_EASY_2 = ReviewTask(
    task_id="easy_hardcoded_secret",
    difficulty="easy",
    language="python",
    context="A script that sends emails using SMTP.",
    code_snippet='''import smtplib
from email.mime.text import MIMEText

def send_email(to_addr, subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = "admin@company.com"
    password = "SuperSecret123!"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = to_addr

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(username, password)
    server.sendmail(username, to_addr, msg.as_string())
    server.quit()
''',
    expected_issues=[
        "hardcoded password, hardcoded secret, credentials in code, plaintext password",
        "no error handling, no try, exception",
        "no input validation, email validation",
    ],
    issue_severities={
        "Hardcoded credentials": "critical",
        "No error handling": "medium",
        "No input validation": "low",
    },
    grader=lambda ids, review: _keyword_match_score(ids, review, [
        "hardcoded password, hardcoded secret, credentials in code, plaintext password",
        "no error handling, no try, exception",
        "no input validation, email validation",
    ]),
)


# ============================================================
# MEDIUM TASKS
# ============================================================

TASK_MEDIUM_1 = ReviewTask(
    task_id="medium_race_condition",
    difficulty="medium",
    language="python",
    context="A bank account class used in a multi-threaded web application.",
    code_snippet='''class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance

    def deposit(self, amount):
        current = self.balance
        # simulate processing delay
        self.balance = current + amount
        return self.balance

    def withdraw(self, amount):
        if self.balance >= amount:
            current = self.balance
            self.balance = current - amount
            return self.balance
        return None

    def transfer(self, other_account, amount):
        result = self.withdraw(amount)
        if result is not None:
            other_account.deposit(amount)
            return True
        return False
''',
    expected_issues=[
        "race condition, thread safety, concurrent, lock, mutex, synchronization",
        "no atomicity, non-atomic, transfer not atomic",
        "withdraw returns none, error handling, insufficient funds",
        "no logging, audit trail, transaction log",
    ],
    issue_severities={
        "Race condition": "critical",
        "Non-atomic transfer": "high",
        "Poor error signaling": "medium",
        "No audit logging": "low",
    },
    grader=lambda ids, review: _keyword_match_score(ids, review, [
        "race condition, thread safety, concurrent, lock, mutex, synchronization",
        "no atomicity, non-atomic, transfer not atomic",
        "withdraw returns none, error handling, insufficient funds",
        "no logging, audit trail, transaction log",
    ]),
)

TASK_MEDIUM_2 = ReviewTask(
    task_id="medium_path_traversal",
    difficulty="medium",
    language="python",
    context="A file server API that serves user-uploaded documents.",
    code_snippet='''from flask import Flask, request, send_file
import os

app = Flask(__name__)
UPLOAD_DIR = "/var/uploads"

@app.route("/download")
def download_file():
    filename = request.args.get("file")
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return {"error": "File not found"}, 404

@app.route("/upload", methods=["POST"])
def upload_file():
    f = request.files["document"]
    save_path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(save_path)
    return {"status": "uploaded", "filename": f.filename}
''',
    expected_issues=[
        "path traversal, directory traversal, ../, dot dot slash",
        "no file type validation, file extension, mime type, content type",
        "no file size limit, denial of service, large file",
        "no authentication, authorization, access control",
    ],
    issue_severities={
        "Path traversal": "critical",
        "No file type validation": "high",
        "No file size limit": "medium",
        "No authentication": "high",
    },
    grader=lambda ids, review: _keyword_match_score(ids, review, [
        "path traversal, directory traversal, ../, dot dot slash",
        "no file type validation, file extension, mime type, content type",
        "no file size limit, denial of service, large file",
        "no authentication, authorization, access control",
    ]),
)


# ============================================================
# HARD TASKS
# ============================================================

TASK_HARD_1 = ReviewTask(
    task_id="hard_jwt_auth",
    difficulty="hard",
    language="python",
    context="A JWT authentication middleware for a REST API handling sensitive user data.",
    code_snippet='''import jwt
import time
from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = "my-secret-key"

def create_token(user_id, role="user"):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": time.time() + 86400 * 30  # 30 days
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256", "none"])
            request.user = data
        except:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/users")
@require_auth
def admin_users():
    if request.user.get("role") == "admin":
        return jsonify({"users": ["alice", "bob", "charlie"]})
    return jsonify({"error": "Forbidden"}), 403

@app.route("/profile")
@require_auth
def profile():
    return jsonify({"user_id": request.user["user_id"]})
''',
    expected_issues=[
        "none algorithm, algorithm none, alg none, jwt none attack",
        "weak secret, hardcoded secret, secret key, brute force",
        "token expiry too long, 30 days, expiration",
        "bare except, exception handling, swallow exception",
        "no token prefix, bearer, authorization header format",
        "no rate limiting, brute force, rate limit",
        "role in token, privilege escalation, role manipulation",
    ],
    issue_severities={
        "Algorithm none attack": "critical",
        "Weak/hardcoded secret": "critical",
        "Excessive token lifetime": "high",
        "Bare except clause": "medium",
        "No Bearer prefix check": "low",
        "No rate limiting": "medium",
        "Role stored in token": "high",
    },
    grader=lambda ids, review: _keyword_match_score(ids, review, [
        "none algorithm, algorithm none, alg none, jwt none attack",
        "weak secret, hardcoded secret, secret key, brute force",
        "token expiry too long, 30 days, expiration",
        "bare except, exception handling, swallow exception",
        "no token prefix, bearer, authorization header format",
        "no rate limiting, brute force, rate limit",
        "role in token, privilege escalation, role manipulation",
    ]),
)


# ============================================================
# ALL TASKS
# ============================================================

ALL_TASKS = [
    TASK_EASY_1,
    TASK_EASY_2,
    TASK_MEDIUM_1,
    TASK_MEDIUM_2,
    TASK_HARD_1,
]

TASKS_BY_ID = {t.task_id: t for t in ALL_TASKS}
TASKS_BY_DIFFICULTY = {
    "easy": [t for t in ALL_TASKS if t.difficulty == "easy"],
    "medium": [t for t in ALL_TASKS if t.difficulty == "medium"],
    "hard": [t for t in ALL_TASKS if t.difficulty == "hard"],
}
