"""
FastAPI server for ModelJury-Env.

Endpoints:
  GET  /health          — liveness probe
  POST /reset           — start new episode
  POST /step            — take an action
  GET  /state/{id}      — current env state
  GET  /docs            — Swagger UI (auto-generated)
"""
import uuid
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel

from .env import ModelJuryEnv
from .models import ModelJuryAction, ModelJuryObservation, ModelJuryReward, ModelJuryState

app = FastAPI(
    title="ModelJury-Env",
    description=(
        "An OpenEnv environment where AI agents learn to evaluate other LLMs: "
        "detecting hallucinations, tracing reasoning errors, and ranking response quality."
    ),
    version="0.1.0",
)

# Session store: session_id → ModelJuryEnv instance
_sessions: Dict[str, ModelJuryEnv] = {}


class ResetRequest(BaseModel):
    """Reset payload compatible with OpenEnv validators.

    Accepts either `task_type` (preferred) or `task` (compat alias).
    """
    task_type: Optional[str] = None
    task: Optional[str] = None
    scenario_id: Optional[str] = None
    session_id: Optional[str] = None
    seed: Optional[int] = None


class ResetResponse(BaseModel):
    session_id: str
    observation: ModelJuryObservation


class StepRequest(BaseModel):
    session_id: str
    action: ModelJuryAction


class StepResponse(BaseModel):
    observation: ModelJuryObservation
    reward: float
    reward_breakdown: Dict[str, float]
    feedback: str
    done: bool
    info: dict


class StateResponse(BaseModel):
    session_id: str
    state: ModelJuryState


@app.get("/health")
def health():
    return {"status": "healthy", "env": "modeljury-env", "version": "0.1.0"}


@app.post("/reset", response_model=ResetResponse)
def reset(req: Optional[ResetRequest] = Body(default=None)):
    """Start a new episode. Returns the first observation.

    Works with empty POST bodies to satisfy automated validators.
    """
    req = req or ResetRequest()
    task_type = req.task_type or req.task or "hallucination"

    if task_type not in ("hallucination", "reasoning", "ranking"):
        raise HTTPException(
            status_code=400,
            detail="task_type must be 'hallucination', 'reasoning', or 'ranking'",
        )

    session_id = req.session_id or str(uuid.uuid4())
    env = ModelJuryEnv(seed=req.seed)
    _sessions[session_id] = env

    obs = env.reset(task_type=task_type, scenario_id=req.scenario_id)
    return ResetResponse(session_id=session_id, observation=obs)


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    """Take one action in the current episode."""
    env = _sessions.get(req.session_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Session '{req.session_id}' not found. Call /reset first.")

    try:
        obs, reward_obj, done, info = env.step(req.action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return StepResponse(
        observation=obs,
        reward=reward_obj.score,
        reward_breakdown=reward_obj.breakdown,
        feedback=reward_obj.feedback,
        done=done,
        info=info,
    )


@app.get("/state/{session_id}", response_model=StateResponse)
def state(session_id: str):
    """Get current environment state for a session."""
    env = _sessions.get(session_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return StateResponse(session_id=session_id, state=env.state())


@app.get("/")
def root():
    return {
        "name": "ModelJury-Env",
        "description": "AI agents learn to evaluate other AI models",
        "tasks": ["hallucination", "reasoning", "ranking"],
        "docs": "/docs",
        "health": "/health",
    }
