"""Type-safe models for the Code Review environment."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class Action(BaseModel):
    """Base action."""
    metadata: Dict[str, Any] = {}


class Observation(BaseModel):
    """Base observation."""
    done: bool = False
    reward: Optional[float] = None
    metadata: Dict[str, Any] = {}


class State(BaseModel):
    """Base state."""
    episode_id: Optional[str] = None
    step_count: int = 0


# --- Code Review specific models ---

class CodeReviewAction(Action):
    """Agent submits a code review with identified issues."""
    review: str  # The agent's review text
    identified_issues: List[str] = []  # List of issues found
    severity_ratings: Dict[str, str] = {}  # issue -> "low"/"medium"/"high"/"critical"
    suggested_fixes: List[str] = []  # Suggested code fixes


class CodeReviewObservation(Observation):
    """What the agent sees."""
    task_id: str = ""
    task_difficulty: str = ""  # "easy", "medium", "hard"
    code_snippet: str = ""
    language: str = ""
    context: str = ""  # Description of what the code should do
    known_issue_count: int = 0  # How many issues exist (hint)
    feedback: str = ""  # Feedback after review submission
    score: float = 0.0  # Grader score 0.0-1.0


class CodeReviewState(State):
    """Episode metadata."""
    current_task_id: str = ""
    current_difficulty: str = ""
    tasks_completed: int = 0
    total_score: float = 0.0
