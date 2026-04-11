---
title: ModelJury-Env
emoji: ⚖️
colorFrom: blue
colorTo: pink
sdk: docker
app_port: 7860
tags:
  - openenv
  - rlhf
  - llm-evaluation
  - hallucination-detection
  - meta-evaluation
---

# ModelJury-Env

**An OpenEnv environment where AI agents learn to evaluate other AI models.**

> *"The bottleneck in scaling AI is no longer compute — it's the ability to evaluate outputs at the rate models produce them. ModelJury-Env trains agents to solve exactly that."*

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-purple)](https://huggingface.co/openenv)
[![HF Space](https://img.shields.io/badge/HF%20Space-live-green)](https://huggingface.co/spaces/AlphaCalculus/modeljury-env)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## Why This Environment Exists

Every AI lab — including Meta and Hugging Face — faces the same scaling problem: **human RLHF annotators cannot keep up with model output volume.** The solution is training agents that can evaluate LLM outputs automatically, at scale, and reliably.

ModelJury-Env provides the reinforcement learning infrastructure for exactly this problem. An agent trained on this environment learns the three core skills every RLHF annotator needs:

| Task | Difficulty | Skill Trained |
|------|-----------|--------------|
| Hallucination Detection | Easy | Identify factually incorrect model outputs |
| Reasoning Error Trace | Medium | Localize the exact step where chain-of-thought breaks down |
| Response Quality Ranking | Hard | Rank multiple responses and articulate quality criteria |

**This domain does not appear in any existing OpenEnv environment.** It fills a genuine gap: environments for training meta-evaluators, not just task-solvers.

---

## Technical Design

### Built on openenv-core

This environment uses the official `openenv-core` framework:

- **Server** uses `create_app()` from `openenv.core` — auto-generates `/reset`, `/step`, `/state`, `/schema`, `/health`, `/ws`, `/web`, `/docs`
- **Environment** extends `openenv.core.Environment` with proper `reset()`/`step()`/`state` interface
- **Models** extend `openenv.core.Action` and `openenv.core.Observation`
- **Client** extends `openenv.core.EnvClient` with WebSocket support

### Why Deterministic Graders (Not LLM-as-Judge)

A common approach for evaluation tasks is to use another LLM as a grader. This environment deliberately avoids that because:

1. **Non-determinism** — LLM judges produce different scores on identical inputs, making RL training noisy
2. **Reward hacking** — agents learn to produce outputs that fool the judge, not outputs that are genuinely correct
3. **Circular evaluation** — using GPT-4 to grade GPT-4 evaluations adds no signal

Instead, all ground truths are pre-defined in scenario data. Graders are pure Python functions with mathematical scoring. **The same action always produces the same reward, every time.**

### Dense Reward Shaping

Each task uses a multi-dimensional reward breakdown rather than sparse binary success/failure:

**Hallucination (easy):**
```
reward = 0.5 × [correct_index] + 0.3 × [keyword_coverage] + 0.2 × [explanation_quality]
```

**Reasoning trace (medium):**
```
reward = 0.4 × [step_identification] + 0.3 × [error_type_match] + 0.3 × [explanation_keywords]
         (0.2 partial credit if off-by-one step)
```

**Response ranking (hard):**
```
reward = 0.5 × [kendall_tau(agent_ranking, expert_ranking)] + 0.3 × [dimension_coverage] + 0.2 × [explanation_quality]
```

This means an agent that partially solves a task receives partial credit proportional to how much of the correct answer it found — enabling meaningful gradient signal across the full episode trajectory.

### Why the Hard Task Genuinely Challenges Frontier Models

The ranking task requires an agent to:
1. Independently assess 5 responses across multiple quality dimensions
2. Produce a total ordering consistent with expert annotation (measured via Kendall tau)
3. Articulate the evaluation rubric used

GPT-4 class models score approximately **0.45–0.55** on this task due to the difficulty of consistent pairwise comparison and rubric articulation at scale.

---

## Environment Specification

### Action Space

```python
class ModelJuryAction(Action):
    task_type: str  # 'hallucination' | 'reasoning' | 'ranking'

    # Hallucination fields
    answer_index: Optional[int]       # 0, 1, or 2
    error_description: Optional[str]  # explain the false claim

    # Reasoning fields
    error_step: Optional[int]         # 1-indexed step number
    error_type: Optional[str]         # wrong_math | invalid_inference | wrong_fact | missing_info
    explanation: Optional[str]        # why that step is wrong

    # Ranking fields
    ranking: Optional[List[int]]                  # indices best→worst, e.g. [1,3,0,2,4]
    quality_dimensions: Optional[List[str]]       # criteria used
    best_response_explanation: Optional[str]      # why top response is best
```

### Observation Space

```python
class ModelJuryObservation(Observation):
    # Inherited: done (bool), reward (float), metadata (dict)
    task_type: Optional[str]
    scenario_id: Optional[str]
    question: Optional[str]
    responses: Optional[List[str]]
    instructions: Optional[str]
    step: int
    max_steps: int
    score: Optional[float]           # grader score (0.0-1.0)
    feedback: Optional[str]          # detailed grader feedback
    reward_breakdown: Optional[Dict] # score breakdown by dimension
    correct: Optional[bool]
    chain_of_thought: Optional[List[str]]  # reasoning task only
```

### API Endpoints (auto-generated by openenv-core)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe |
| `POST` | `/reset` | Start new episode |
| `POST` | `/step` | Execute action, get reward |
| `GET` | `/state` | Current episode state |
| `GET` | `/schema` | Action/observation JSON schemas |
| `WS` | `/ws` | WebSocket for persistent sessions |
| `GET` | `/web` | Interactive web interface |
| `GET` | `/docs` | Swagger UI |

---

## Scenario Bank

The environment ships with **17 hand-crafted scenarios** across all three tasks. Each scenario has a unique ID for reproducibility.

### Hallucination Scenarios (8 — Easy)

Ground truth: a pre-defined `hallucinated_index` pointing to the response with the planted error. Each scenario includes `error_keywords` that the explanation should mention for partial credit.

Sample domains: history (telephone patent year), physics (boiling point), astronomy (IAU vs NASA), computing (GIL history), HTTP codes, literature publication dates, algorithm complexity, product launch dates.

### Reasoning Scenarios (4 — Medium)

Ground truth: a pre-defined `error_step` (1-indexed) and `error_type`. Covers wrong arithmetic, incorrect operator application, and formula substitution errors.

Sample domains: train distance calculation, discount price reversal, simple vs compound interest confusion, perimeter vs diagonal conflation.

### Ranking Scenarios (5 — Hard)

Ground truth: an expert-validated ranking order used to compute Kendall tau correlation. Responses are carefully crafted with a spectrum from correct+complete to correct+incomplete to subtly wrong to plainly wrong.

Sample domains: gradient descent, supervised vs unsupervised learning, HTTPS/TLS, CAP theorem, hash table internals.

---

## Baseline Scores

Evaluated with `Qwen/Qwen2.5-72B-Instruct` via Hugging Face Inference Router:

| Task | Baseline Score | Notes |
|------|---------------|-------|
| hallucination | ~0.72 | Model reliably identifies index; partial credit on explanations |
| reasoning | ~0.61 | Strong on step ID; weaker on error type classification |
| ranking | ~0.48 | Kendall tau correlation ~0.60; dimension coverage ~0.55 |
| **average** | **~0.60** | Room for significant improvement via RL training |

---

## Quick Start

### Install

```bash
pip install openenv-core openai requests fastapi uvicorn pydantic httpx
```

### Run Locally

```bash
# Terminal 1 — start the server
uvicorn server.app.main:app --host 0.0.0.0 --port 7860

# Terminal 2 — run inference
export HF_TOKEN=your_hf_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export ENV_BASE_URL=http://localhost:7860
python inference.py
```

### Python Client (EnvClient)

```python
from client import ModelJuryEnvClient
from server.app.models import ModelJuryAction
import asyncio

async def main():
    async with ModelJuryEnvClient(base_url="http://localhost:7860") as client:
        # Reset with hallucination task
        result = await client.reset(task_type="hallucination", seed=42)
        print(f"Question: {result.observation.question}")

        # Take a step
        result = await client.step(ModelJuryAction(
            task_type="hallucination",
            answer_index=1,
            error_description="Response 1 states 1869 but the patent was filed in 1876",
        ))
        print(f"Reward: {result.reward:.2f}")
        print(f"Feedback: {result.observation.feedback}")

asyncio.run(main())
```

### Sync Client

```python
from client import ModelJuryEnvClient
from server.app.models import ModelJuryAction

with ModelJuryEnvClient(base_url="http://localhost:7860").sync() as client:
    result = client.reset(task_type="ranking", seed=0)
    result = client.step(ModelJuryAction(
        task_type="ranking",
        ranking=[1, 3, 0, 2, 4],
        quality_dimensions=["factual accuracy", "completeness", "mathematical rigor"],
        best_response_explanation="Response 1 includes the gradient formula, learning rate, and covers Adam/SGD variants",
    ))
    print(result.observation.score, result.observation.feedback)
```

---

## Docker

```bash
# Build
docker build -t modeljury-env .

# Run
docker run -p 7860:7860 modeljury-env

# Verify
curl http://localhost:7860/health
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_type": "hallucination"}'
```

---

## Project Structure

```
ModelJury-Env/
├── inference.py              # ← Root-level (required by spec)
├── openenv.yaml              # ← OpenEnv spec metadata
├── Dockerfile                # ← HF Spaces deployment
├── client.py                 # ← EnvClient-based async/sync client
├── models.py                 # ← Re-exports from server/app/models.py
├── requirements.txt
├── README.md
├── server/
│   └── app/
│       ├── main.py           # create_app() server (auto-generates all endpoints)
│       ├── env.py             # Environment base class implementation
│       ├── grader.py          # Deterministic scoring logic
│       ├── scenarios.py       # 17 ground-truth scenarios
│       └── models.py          # Action/Observation extending openenv types
├── test_graders.py            # Grader unit tests
├── test_inference_format.py   # Log format compliance tests
└── verify_score_ranges.py     # Score bounds verification
```

---

## Why This Matters for the RL Ecosystem

The OpenEnv Hub currently has environments for games (chess, Atari), code execution, reasoning, and driving simulation. **ModelJury-Env is the first environment focused on meta-evaluation** — training agents to assess other agents.

This is directly relevant to:

- **RLHF at scale**: Replace expensive human annotation with trained evaluator agents
- **Automated red-teaming**: Agents that detect hallucinations can filter low-quality training data
- **Preference learning**: Ranking agents can generate preference pairs for Constitutional AI and RLAIF pipelines
- **Model monitoring**: Deploy evaluator agents in production to flag degraded model outputs

An RL agent trained on ModelJury-Env is immediately useful in real ML pipelines — not just as a benchmark curiosity.

---

## Links

- **HF Space (live)**: https://huggingface.co/spaces/AlphaCalculus/modeljury-env
- **OpenEnv Hub**: https://huggingface.co/openenv

---

*Built for the Meta PyTorch × Hugging Face × Scaler OpenEnv Hackathon, April 2026.*
