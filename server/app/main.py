"""
FastAPI application for ModelJury-Env.

Uses the openenv-core create_app() factory which auto-generates all
standard OpenEnv endpoints:
  - POST /reset     — start new episode
  - POST /step      — take an action
  - GET  /state     — current env state
  - GET  /schema    — action/observation JSON schemas
  - GET  /health    — liveness probe
  - WS   /ws        — WebSocket for persistent sessions
  - GET  /web       — interactive web interface
  - GET  /docs      — Swagger UI (auto-generated)
"""

from openenv.core import create_app

try:
    from models import ModelJuryAction, ModelJuryObservation
except ImportError:
    from .models import ModelJuryAction, ModelJuryObservation

try:
    from env import ModelJuryEnvironment
except ImportError:
    from .env import ModelJuryEnvironment


# create_app expects a callable (factory) that returns an Environment instance
app = create_app(
    ModelJuryEnvironment,
    ModelJuryAction,
    ModelJuryObservation,
    env_name="modeljury_env",
    max_concurrent_envs=10,
)


def main() -> None:
    """Console entrypoint for local server startup."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)
