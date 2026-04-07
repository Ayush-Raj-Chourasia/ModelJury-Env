from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ModelJuryAction(BaseModel):
    """
    Unified action model for all three tasks.

    For task_type='hallucination':
        - answer_index: which response (0,1,2) is hallucinated
        - error_description: explain what is wrong

    For task_type='reasoning':
        - error_step: which step number (1-indexed) has the error
        - error_type: one of 'wrong_math', 'invalid_inference', 'wrong_fact', 'missing_info'
        - explanation: why that step is wrong

    For task_type='ranking':
        - ranking: list of 5 response indices ordered best→worst, e.g. [2,0,4,1,3]
        - quality_dimensions: list of criteria you used, e.g. ['factual accuracy', 'completeness']
        - best_response_explanation: why your top-ranked response is the best
    """
    task_type: str = Field(..., description="'hallucination', 'reasoning', or 'ranking'")
    answer_index: Optional[int] = Field(None, description="Index of hallucinated answer (0,1,2)")
    error_description: Optional[str] = Field(None, description="Explanation of the hallucination")
    error_step: Optional[int] = Field(None, description="1-indexed step number with the error")
    error_type: Optional[str] = Field(None, description="wrong_math|invalid_inference|wrong_fact|missing_info")
    explanation: Optional[str] = Field(None, description="Why that step is wrong")
    ranking: Optional[List[int]] = Field(None, description="Response indices best→worst")
    quality_dimensions: Optional[List[str]] = Field(None, description="Criteria used for ranking")
    best_response_explanation: Optional[str] = Field(None, description="Why top response is best")


class ModelJuryObservation(BaseModel):
    """Observation returned to the agent at each step."""
    task_type: str
    scenario_id: str
    question: str
    responses: List[str]
    instructions: str
    step: int
    max_steps: int
    previous_feedback: Optional[str] = None
    chain_of_thought: Optional[List[str]] = None  # for reasoning task only
    metadata: Optional[Dict[str, Any]] = None


class ModelJuryReward(BaseModel):
    score: float
    breakdown: Dict[str, float]
    feedback: str
    correct: bool


class ModelJuryState(BaseModel):
    task_type: str
    scenario_id: str
    step: int
    done: bool
    cumulative_score: float
    last_reward: Optional[float] = None
