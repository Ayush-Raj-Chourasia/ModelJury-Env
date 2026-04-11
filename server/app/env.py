"""
ModelJury-Env — core environment class.

Extends openenv.core.Environment so the framework can manage sessions,
WebSocket connections, and automated evaluation.

Tasks:
  - hallucination (easy):   Detect which of 3 LLM responses contains a factual error
  - reasoning     (medium): Identify the exact step where chain-of-thought breaks down
  - ranking       (hard):   Rank 5 LLM responses by quality and articulate evaluation criteria
"""
import random
from typing import Optional, Any
from uuid import uuid4

from openenv.core import Environment
from openenv.core.env_server.types import State

from .models import ModelJuryAction, ModelJuryObservation
from .grader import grade
from .scenarios import get_scenarios


TASK_INSTRUCTIONS = {
    "hallucination": (
        "You are given a factual question and three LLM-generated responses. "
        "Exactly ONE response contains a factual error (hallucination). "
        "Identify which response (0, 1, or 2) is hallucinated and explain the specific false claim."
    ),
    "reasoning": (
        "You are given a problem and an LLM's step-by-step solution. "
        "Exactly ONE step contains an error (wrong math, wrong fact, or invalid inference). "
        "Identify the step number (1-indexed), the error type, and explain what is wrong."
    ),
    "ranking": (
        "You are given a question and five LLM-generated responses (indexed 0-4). "
        "Rank all five from best to worst quality. "
        "Provide the ranking as a list of indices (best first), list the quality dimensions you used, "
        "and explain why your top-ranked response is the best."
    ),
}

MAX_STEPS = 1  # Single-turn per episode


class ModelJuryEnvironment(Environment):
    """
    ModelJury environment — agents learn to evaluate other AI models.

    Episode flow:
        obs = reset(task_type='hallucination')
        obs = step(ModelJuryAction(...))
        # obs.done == True, obs.reward == score
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize with no transform or rubric."""
        super().__init__()
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_scenario = None
        self._current_task_type = None
        self._rng = random.Random()

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task_type: str = "hallucination",
        scenario_id: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelJuryObservation:
        """
        Reset the environment and return an initial observation.

        Args:
            seed: Random seed for scenario selection
            episode_id: Optional episode ID
            task_type: 'hallucination', 'reasoning', or 'ranking'
            scenario_id: Optional specific scenario ID for reproducibility
        """
        if seed is not None:
            self._rng = random.Random(seed)

        if task_type not in ("hallucination", "reasoning", "ranking"):
            task_type = "hallucination"

        scenarios = get_scenarios(task_type)
        if scenario_id:
            matching = [s for s in scenarios if s["id"] == scenario_id]
            if not matching:
                # Fall back to random
                self._current_scenario = self._rng.choice(scenarios)
            else:
                self._current_scenario = matching[0]
        else:
            self._current_scenario = self._rng.choice(scenarios)

        self._current_task_type = task_type
        self._state = State(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
        )

        return self._build_observation()

    def step(
        self,
        action: ModelJuryAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> ModelJuryObservation:
        """
        Execute one step: grade the agent's evaluation.

        Returns observation with done=True, reward=score.
        """
        self._state.step_count += 1

        if self._current_scenario is None:
            return ModelJuryObservation(
                done=True,
                reward=0.0,
                score=0.0,
                feedback="No active episode. Call reset() first.",
            )

        # Build action dict for grader
        action_dict = {
            "task_type": action.task_type,
            "answer_index": action.answer_index,
            "error_description": action.error_description,
            "error_step": action.error_step,
            "error_type": action.error_type,
            "explanation": action.explanation,
            "ranking": action.ranking,
            "quality_dimensions": action.quality_dimensions,
            "best_response_explanation": action.best_response_explanation,
        }

        result = grade(
            task_type=self._current_task_type,
            action=action_dict,
            ground_truth=self._current_scenario,
        )

        score = result["score"]
        return ModelJuryObservation(
            task_type=self._current_task_type,
            scenario_id=self._current_scenario["id"],
            question=self._current_scenario["question"],
            responses=self._get_responses(),
            instructions=TASK_INSTRUCTIONS[self._current_task_type],
            step=self._state.step_count,
            max_steps=MAX_STEPS,
            score=score,
            feedback=result["feedback"],
            reward_breakdown=result["breakdown"],
            correct=result["correct"],
            chain_of_thought=self._current_scenario.get("chain_of_thought") if self._current_task_type == "reasoning" else None,
            done=True,
            reward=score,
            metadata={
                "scenario_id": self._current_scenario["id"],
                "task_type": self._current_task_type,
                "breakdown": result["breakdown"],
            },
        )

    @property
    def state(self) -> State:
        """Get current environment state."""
        return self._state

    def _get_responses(self):
        """Get the appropriate responses list for the current task."""
        s = self._current_scenario
        if self._current_task_type == "reasoning":
            return s.get("chain_of_thought", [])
        return s.get("responses", [])

    def _build_observation(self) -> ModelJuryObservation:
        """Build the initial observation (before step)."""
        s = self._current_scenario
        task = self._current_task_type

        responses = self._get_responses()
        chain_of_thought = s.get("chain_of_thought") if task == "reasoning" else None

        obs_metadata = {}
        if task == "reasoning":
            obs_metadata["available_error_types"] = [
                "wrong_math", "invalid_inference", "wrong_fact", "missing_info"
            ]

        return ModelJuryObservation(
            task_type=task,
            scenario_id=s["id"],
            question=s["question"],
            responses=responses,
            instructions=TASK_INSTRUCTIONS[task],
            step=0,
            max_steps=MAX_STEPS,
            chain_of_thought=chain_of_thought,
            done=False,
            reward=0.0,
            metadata=obs_metadata,
        )
