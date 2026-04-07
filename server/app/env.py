"""
ModelJury-Env — core environment class.

An AI agent learns to evaluate other AI models:
  - Task 1 (easy):   Hallucination detection
  - Task 2 (medium): Reasoning error localization
  - Task 3 (hard):   Comparative response ranking

All three tasks share the same step()/reset()/state() interface.
"""
import random
from typing import Optional, Dict, Any

from .models import (
    ModelJuryAction,
    ModelJuryObservation,
    ModelJuryReward,
    ModelJuryState,
)
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

MAX_STEPS = 1  # Single-turn per episode (agent gets one shot)


class ModelJuryEnv:
    """
    ModelJury environment.

    Episode flow:
        obs = reset(task_type=...)    # choose 'hallucination', 'reasoning', or 'ranking'
        result = step(action)         # action is ModelJuryAction
        # result contains (observation, reward, done, info)
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._current_scenario: Optional[Dict[str, Any]] = None
        self._current_task_type: Optional[str] = None
        self._step_count = 0
        self._done = False
        self._cumulative_score = 0.0
        self._last_reward: Optional[float] = None

    def reset(self, task_type: str = "hallucination", scenario_id: Optional[str] = None) -> ModelJuryObservation:
        """
        Reset the environment and return an initial observation.

        Args:
            task_type: 'hallucination', 'reasoning', or 'ranking'
            scenario_id: optional specific scenario ID for reproducibility
        """
        scenarios = get_scenarios(task_type)
        if scenario_id:
            matching = [s for s in scenarios if s["id"] == scenario_id]
            if not matching:
                raise ValueError(f"Scenario '{scenario_id}' not found for task '{task_type}'")
            self._current_scenario = matching[0]
        else:
            self._current_scenario = self._rng.choice(scenarios)

        self._current_task_type = task_type
        self._step_count = 0
        self._done = False
        self._cumulative_score = 0.0
        self._last_reward = None

        return self._build_observation(previous_feedback=None)

    def step(self, action: ModelJuryAction):
        """
        Execute one step with the given action.

        Returns:
            (observation, reward, done, info)
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() first.")
        if self._current_scenario is None:
            raise RuntimeError("No active episode. Call reset() first.")

        self._step_count += 1

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

        reward_val = result["score"]
        self._cumulative_score += reward_val
        self._last_reward = reward_val
        self._done = True  # single-turn episodes

        reward = ModelJuryReward(
            score=reward_val,
            breakdown=result["breakdown"],
            feedback=result["feedback"],
            correct=result["correct"],
        )

        obs = self._build_observation(previous_feedback=result["feedback"])
        info = {
            "scenario_id": self._current_scenario["id"],
            "task_type": self._current_task_type,
            "breakdown": result["breakdown"],
        }

        return obs, reward, self._done, info

    def state(self) -> ModelJuryState:
        """Return current environment state."""
        return ModelJuryState(
            task_type=self._current_task_type or "unknown",
            scenario_id=self._current_scenario["id"] if self._current_scenario else "none",
            step=self._step_count,
            done=self._done,
            cumulative_score=self._cumulative_score,
            last_reward=self._last_reward,
        )

    def _build_observation(self, previous_feedback: Optional[str]) -> ModelJuryObservation:
        s = self._current_scenario
        task = self._current_task_type

        responses = s.get("responses", [])
        chain_of_thought = s.get("chain_of_thought", None)

        # For reasoning task, embed CoT as part of responses list
        if task == "reasoning" and chain_of_thought:
            # responses list will be the chain-of-thought steps
            responses = chain_of_thought

        return ModelJuryObservation(
            task_type=task,
            scenario_id=s["id"],
            question=s["question"],
            responses=responses,
            instructions=TASK_INSTRUCTIONS[task],
            step=self._step_count,
            max_steps=MAX_STEPS,
            previous_feedback=previous_feedback,
            chain_of_thought=chain_of_thought if task == "reasoning" else None,
            metadata={"available_error_types": ["wrong_math", "invalid_inference", "wrong_fact", "missing_info"]}
            if task == "reasoning" else None,
        )
