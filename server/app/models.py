"""
Data models for ModelJury-Env.

Models extend the OpenEnv base types (Action, Observation) so the
environment is fully compatible with the openenv-core framework,
including WebSocket sessions, schema discovery, and agentic evaluation.
"""
from typing import Optional, List, Dict, Any

from openenv.core import Action, Observation
from pydantic import Field


class ModelJuryAction(Action):
    """
    Unified action model for all three ModelJury tasks.

    For task_type='hallucination':
        - answer_index: which response (0,1,2) is hallucinated
        - error_description: explain what is wrong

    For task_type='reasoning':
        - error_step: which step number (1-indexed) has the error
        - error_type: one of 'wrong_math', 'invalid_inference', 'wrong_fact', 'missing_info'
        - explanation: why that step is wrong

    For task_type='ranking':
        - ranking: list of 5 response indices ordered best→worst, e.g. [2,0,4,1,3]
        - quality_dimensions: list of criteria you used
        - best_response_explanation: why your top-ranked response is the best
    """
    task_type: str = Field(..., description="'hallucination', 'reasoning', or 'ranking'")

    # Hallucination fields
    answer_index: Optional[int] = Field(None, description="Index of hallucinated answer (0,1,2)")
    error_description: Optional[str] = Field(None, description="Explanation of the hallucination")

    # Reasoning fields
    error_step: Optional[int] = Field(None, description="1-indexed step number with the error")
    error_type: Optional[str] = Field(None, description="wrong_math|invalid_inference|wrong_fact|missing_info")
    explanation: Optional[str] = Field(None, description="Why that step is wrong")

    # Ranking fields
    ranking: Optional[List[int]] = Field(None, description="Response indices best→worst")
    quality_dimensions: Optional[List[str]] = Field(None, description="Criteria used for ranking")
    best_response_explanation: Optional[str] = Field(None, description="Why top response is best")


class ModelJuryObservation(Observation):
    """
    Observation returned to the agent.

    Inherits from openenv Observation which provides:
        - done: bool (whether episode has terminated)
        - reward: Optional[float] (reward signal from last action)
        - metadata: Dict[str, Any] (additional metadata)
    """
    task_type: Optional[str] = Field(None, description="Current task type")
    scenario_id: Optional[str] = Field(None, description="Scenario identifier")
    question: Optional[str] = Field(None, description="The question to evaluate")
    responses: Optional[List[str]] = Field(None, description="LLM responses to evaluate")
    instructions: Optional[str] = Field(None, description="Task-specific instructions")
    step: int = Field(0, description="Current step number")
    max_steps: int = Field(1, description="Max steps per episode")

    # Feedback fields (populated after step)
    score: Optional[float] = Field(None, description="Score from grader (0.0-1.0)")
    feedback: Optional[str] = Field(None, description="Detailed feedback from grader")
    reward_breakdown: Optional[Dict[str, float]] = Field(None, description="Score breakdown by dimension")
    correct: Optional[bool] = Field(None, description="Whether the answer was correct")

    # Reasoning-specific
    chain_of_thought: Optional[List[str]] = Field(None, description="CoT steps (reasoning task)")
