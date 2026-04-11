"""
client.py — Python client for ModelJury-Env.

Extends openenv.core.EnvClient for full compatibility with the
OpenEnv framework (WebSocket sessions, schema discovery, etc).

Usage (async):
    from client import ModelJuryEnvClient
    from server.app.models import ModelJuryAction

    async with ModelJuryEnvClient(base_url="http://localhost:7860") as client:
        result = await client.reset(task_type="hallucination")
        print(result.observation.question)

        result = await client.step(ModelJuryAction(
            task_type="hallucination",
            answer_index=1,
            error_description="The year 1869 is wrong — patent was filed in 1876",
        ))
        print(result.observation.reward, result.observation.feedback)

Usage (sync):
    from client import ModelJuryEnvClient
    from server.app.models import ModelJuryAction

    with ModelJuryEnvClient(base_url="http://localhost:7860").sync() as client:
        result = client.reset(task_type="hallucination")
        result = client.step(ModelJuryAction(task_type="hallucination", answer_index=1, error_description="..."))
"""
from typing import Dict, Optional, Any

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from server.app.models import ModelJuryAction, ModelJuryObservation


class ModelJuryEnvClient(EnvClient[ModelJuryAction, ModelJuryObservation, State]):
    """
    Client for ModelJury-Env.

    Maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    """

    def _step_payload(self, action: ModelJuryAction) -> Dict:
        """Convert ModelJuryAction to JSON payload."""
        payload = {"task_type": action.task_type}
        if action.answer_index is not None:
            payload["answer_index"] = action.answer_index
        if action.error_description is not None:
            payload["error_description"] = action.error_description
        if action.error_step is not None:
            payload["error_step"] = action.error_step
        if action.error_type is not None:
            payload["error_type"] = action.error_type
        if action.explanation is not None:
            payload["explanation"] = action.explanation
        if action.ranking is not None:
            payload["ranking"] = action.ranking
        if action.quality_dimensions is not None:
            payload["quality_dimensions"] = action.quality_dimensions
        if action.best_response_explanation is not None:
            payload["best_response_explanation"] = action.best_response_explanation
        return payload

    def _parse_result(self, payload: Dict) -> StepResult[ModelJuryObservation]:
        """Parse server response into StepResult."""
        obs_data = payload.get("observation", {})
        observation = ModelJuryObservation(
            task_type=obs_data.get("task_type"),
            scenario_id=obs_data.get("scenario_id"),
            question=obs_data.get("question"),
            responses=obs_data.get("responses"),
            instructions=obs_data.get("instructions"),
            step=obs_data.get("step", 0),
            max_steps=obs_data.get("max_steps", 1),
            score=obs_data.get("score"),
            feedback=obs_data.get("feedback"),
            reward_breakdown=obs_data.get("reward_breakdown"),
            correct=obs_data.get("correct"),
            chain_of_thought=obs_data.get("chain_of_thought"),
            done=payload.get("done", obs_data.get("done", False)),
            reward=payload.get("reward", obs_data.get("reward")),
            metadata=obs_data.get("metadata", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward", obs_data.get("reward")),
            done=payload.get("done", obs_data.get("done", False)),
        )

    def _parse_state(self, payload: Dict) -> State:
        """Parse server response into State."""
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )


# ── Quick demo ────────────────────────────────────────────────────────────────

async def _demo():
    """Quick async demo — run with python client.py"""
    import asyncio

    BASE_URL = "http://localhost:7860"
    print(f"Connecting to {BASE_URL}...\n")

    try:
        async with ModelJuryEnvClient(base_url=BASE_URL) as client:
            # Reset with hallucination task
            result = await client.reset(task_type="hallucination", seed=42)
            print(f"Question: {result.observation.question}")
            print(f"Responses: {len(result.observation.responses)} responses to evaluate\n")

            # Take a step
            result = await client.step(ModelJuryAction(
                task_type="hallucination",
                answer_index=1,
                error_description="Response 1 contains a wrong year — patent was 1876, not 1869",
            ))
            print(f"Reward: {result.reward}")
            print(f"Score: {result.observation.score}")
            print(f"Feedback: {result.observation.feedback}")
            print(f"Done: {result.done}")

    except Exception as e:
        print(f"Demo failed (server not running?): {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_demo())
