"""
client.py — Python client for ModelJury-Env.

Provides a clean async and sync interface for interacting with
a running ModelJury-Env server (local or Hugging Face Spaces).

Usage (async):
    from client import ModelJuryClient

    async with ModelJuryClient("https://alphacalculus-modeljury-env.hf.space") as client:
        obs = await client.reset("hallucination")
        result = await client.step(obs["session_id"], {
            "task_type": "hallucination",
            "answer_index": 1,
            "error_description": "The year 1869 is wrong — patent was filed in 1876"
        })
        print(result["reward"], result["feedback"])

Usage (sync):
    client = ModelJuryClient.sync("https://alphacalculus-modeljury-env.hf.space")
    obs = client.reset("hallucination")
    result = client.step(obs["session_id"], {...})
"""
import asyncio
import json
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

try:
    import httpx
    _HTTPX = True
except ImportError:
    _HTTPX = False

try:
    import requests as _requests
    _REQUESTS = True
except ImportError:
    _REQUESTS = False


class ModelJuryClientError(Exception):
    pass


class ModelJuryClient:
    """
    Async client for ModelJury-Env.

    Connects to a running ModelJury-Env server and exposes
    reset(), step(), state(), and health() methods.
    """

    def __init__(self, base_url: str = "http://localhost:7860"):
        if not _HTTPX:
            raise ImportError("httpx is required for async client: pip install httpx")
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> "httpx.AsyncClient":
        if self._client is None:
            raise ModelJuryClientError(
                "Client not initialized. Use 'async with ModelJuryClient(...) as client:'"
            )
        return self._client

    async def health(self) -> Dict[str, Any]:
        """Check server health."""
        r = await self._get_client().get("/health")
        r.raise_for_status()
        return r.json()

    async def reset(
        self,
        task_type: str = "hallucination",
        scenario_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Start a new episode.

        Args:
            task_type: 'hallucination', 'reasoning', or 'ranking'
            scenario_id: optional specific scenario ID for reproducibility
            seed: optional random seed

        Returns:
            dict with 'session_id' and 'observation'
        """
        payload: Dict[str, Any] = {"task_type": task_type}
        if scenario_id:
            payload["scenario_id"] = scenario_id
        if seed is not None:
            payload["seed"] = seed

        r = await self._get_client().post("/reset", json=payload)
        r.raise_for_status()
        return r.json()

    async def step(
        self,
        session_id: str,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Take one action in the current episode.

        Args:
            session_id: session ID from reset()
            action: dict matching ModelJuryAction schema

        Returns:
            dict with 'observation', 'reward', 'reward_breakdown', 'feedback', 'done', 'info'
        """
        payload = {"session_id": session_id, "action": action}
        r = await self._get_client().post("/step", json=payload)
        r.raise_for_status()
        return r.json()

    async def state(self, session_id: str) -> Dict[str, Any]:
        """Get current environment state for a session."""
        r = await self._get_client().get(f"/state/{session_id}")
        r.raise_for_status()
        return r.json()

    async def run_episode(
        self,
        task_type: str,
        action: Dict[str, Any],
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Convenience: run a complete single-step episode.

        Returns:
            dict with 'session_id', 'observation', 'reward', 'feedback', 'done'
        """
        reset_data = await self.reset(task_type=task_type, seed=seed)
        session_id = reset_data["session_id"]
        step_result = await self.step(session_id, action)
        return {
            "session_id": session_id,
            "question": reset_data["observation"]["question"],
            "responses": reset_data["observation"]["responses"],
            "reward": step_result["reward"],
            "breakdown": step_result["reward_breakdown"],
            "feedback": step_result["feedback"],
            "done": step_result["done"],
        }

    # ── Sync wrapper ──────────────────────────────────────────────────────────

    @classmethod
    def sync(cls, base_url: str = "http://localhost:7860") -> "_SyncModelJuryClient":
        """Return a synchronous client wrapper."""
        return _SyncModelJuryClient(base_url)


class _SyncModelJuryClient:
    """
    Synchronous wrapper around ModelJuryClient.

    Uses requests directly — no asyncio required.
    """

    def __init__(self, base_url: str = "http://localhost:7860"):
        if not _REQUESTS:
            raise ImportError("requests is required: pip install requests")
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Optional[dict] = None) -> dict:
        r = _requests.post(
            f"{self.base_url}{path}",
            json=payload or {},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def _get(self, path: str) -> dict:
        r = _requests.get(f"{self.base_url}{path}", timeout=30)
        r.raise_for_status()
        return r.json()

    def health(self) -> Dict[str, Any]:
        return self._get("/health")

    def reset(
        self,
        task_type: str = "hallucination",
        scenario_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"task_type": task_type}
        if scenario_id:
            payload["scenario_id"] = scenario_id
        if seed is not None:
            payload["seed"] = seed
        return self._post("/reset", payload)

    def step(self, session_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/step", {"session_id": session_id, "action": action})

    def state(self, session_id: str) -> Dict[str, Any]:
        return self._get(f"/state/{session_id}")

    def run_episode(
        self,
        task_type: str,
        action: Dict[str, Any],
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        reset_data = self.reset(task_type=task_type, seed=seed)
        session_id = reset_data["session_id"]
        step_result = self.step(session_id, action)
        return {
            "session_id": session_id,
            "question": reset_data["observation"]["question"],
            "responses": reset_data["observation"]["responses"],
            "reward": step_result["reward"],
            "breakdown": step_result["reward_breakdown"],
            "feedback": step_result["feedback"],
            "done": step_result["done"],
        }


# ── Quick demo ────────────────────────────────────────────────────────────────

async def _demo():
    """Quick async demo — run with python client.py"""
    BASE_URL = "http://localhost:7860"  # Default to local for testing

    print(f"Connecting to {BASE_URL}...\n")

    try:
        async with ModelJuryClient(BASE_URL) as client:
            h = await client.health()
            print(f"Health: {h}\n")

            # --- Hallucination task ---
            print("── Hallucination task ──")
            result = await client.run_episode(
                task_type="hallucination",
                action={
                    "task_type": "hallucination",
                    "answer_index": 1,
                    "error_description": "Response 1 contains a wrong year — patent was 1876, not 1869",
                },
                seed=42,
            )
            print(f"Q: {result['question']}")
            print(f"Reward: {result['reward']:.2f} | {result['feedback']}\n")
    except Exception as e:
        print(f"Demo failed (server probably not running): {e}")


if __name__ == "__main__":
    asyncio.run(_demo())
