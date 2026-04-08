"""Code Review Environment - server-side logic."""

import uuid
import random
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    CodeReviewAction,
    CodeReviewObservation,
    CodeReviewState,
)
from tasks import ALL_TASKS, TASKS_BY_ID, TASKS_BY_DIFFICULTY


class CodeReviewEnvironment:
    """
    RL environment where an AI agent reviews code snippets for bugs,
    security vulnerabilities, and best-practice violations.

    Implements the OpenEnv interface: reset(), step(), state.
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._state = CodeReviewState()
        self._current_task = None
        self._task_queue = []
        self._episode_scores = []

    def reset(self, seed=None, episode_id=None, **kwargs) -> CodeReviewObservation:
        """Start a new episode. Picks a random task."""
        if seed is not None:
            random.seed(seed)

        # Shuffle tasks for this episode
        self._task_queue = list(ALL_TASKS)
        random.shuffle(self._task_queue)
        self._current_task = self._task_queue[0]
        self._episode_scores = []

        self._state = CodeReviewState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            current_task_id=self._current_task.task_id,
            current_difficulty=self._current_task.difficulty,
            tasks_completed=0,
            total_score=0.0,
        )

        return CodeReviewObservation(
            done=False,
            reward=None,
            task_id=self._current_task.task_id,
            task_difficulty=self._current_task.difficulty,
            code_snippet=self._current_task.code_snippet,
            language=self._current_task.language,
            context=self._current_task.context,
            known_issue_count=len(self._current_task.expected_issues),
            feedback="Review the code snippet and identify all issues.",
            score=0.0,
        )

    def step(self, action: CodeReviewAction, timeout_s=None, **kwargs) -> CodeReviewObservation:
        """Agent submits a code review. Environment grades it."""
        self._state.step_count += 1

        if self._current_task is None:
            return CodeReviewObservation(
                done=True,
                reward=0.0,
                feedback="No active task. Call reset() first.",
                score=0.0,
            )

        # Grade the review
        score = self._current_task.grader(
            action.identified_issues,
            action.review,
        )

        self._episode_scores.append(score)
        self._state.tasks_completed += 1
        self._state.total_score += score

        # Move to next task or finish
        task_idx = self._state.tasks_completed
        has_more = task_idx < len(self._task_queue)

        if has_more:
            self._current_task = self._task_queue[task_idx]
            self._state.current_task_id = self._current_task.task_id
            self._state.current_difficulty = self._current_task.difficulty
        else:
            self._current_task = None

        done = not has_more

        # Build feedback
        feedback_parts = [f"Score: {score:.2f}/{1.0:.2f}"]
        if score >= 0.8:
            feedback_parts.append("Excellent review!")
        elif score >= 0.5:
            feedback_parts.append("Good review, but some issues were missed.")
        else:
            feedback_parts.append("Several important issues were missed.")

        if done:
            avg = self._state.total_score / max(self._state.tasks_completed, 1)
            feedback_parts.append(
                f"Episode complete. Average score: {avg:.2f}"
            )

        # Build next observation
        obs = CodeReviewObservation(
            done=done,
            reward=score,
            task_id=self._current_task.task_id if self._current_task else "",
            task_difficulty=self._current_task.difficulty if self._current_task else "",
            code_snippet=self._current_task.code_snippet if self._current_task else "",
            language=self._current_task.language if self._current_task else "",
            context=self._current_task.context if self._current_task else "",
            known_issue_count=(
                len(self._current_task.expected_issues) if self._current_task else 0
            ),
            feedback=" ".join(feedback_parts),
            score=score,
        )
        return obs

    @property
    def state(self) -> CodeReviewState:
        return self._state
