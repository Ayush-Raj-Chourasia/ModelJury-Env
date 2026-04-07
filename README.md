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
---

# ModelJury-Env

**An OpenEnv environment where AI agents learn to evaluate other AI models.**

> "The ability to evaluate LLM outputs is the most critical skill for scalable AI oversight."

## Overview

ModelJury-Env trains agents in three core LLM evaluation skills that human RLHF annotators perform daily:

| Task | Difficulty | What the Agent Does |
|------|-----------|---------------------|
| Hallucination Detection | Easy | Given 3 responses, identify which one contains a planted factual error |
| Reasoning Error Trace | Medium | Find the exact step in a chain-of-thought where reasoning breaks down |
| Response Quality Ranking | Hard | Rank 5 LLM responses best→worst and write an evaluation rubric |

All graders are **fully deterministic** — ground truths are pre-defined, no LLM-in-grader required.

## Real-World Utility

- Every AI company needs agents that can evaluate model outputs at scale
- RLHF pipelines depend on reliable quality assessment
- Detecting hallucinations is one of the most commercially valuable AI skills
- The hard task (ranking) genuinely challenges frontier models — GPT-4 class models score ~0.4–0.6

## Action Space

```python
class ModelJuryAction(BaseModel):
    task_type: str            # 'hallucination' | 'reasoning' | 'ranking'
    
    # For hallucination task:
    answer_index: Optional[int]          # 0, 1, or 2
    error_description: Optional[str]     # explain the false claim
    
    # For reasoning task:
    error_step: Optional[int]            # 1-indexed step number
    error_type: Optional[str]            # wrong_math|invalid_inference|wrong_fact|missing_info
    explanation: Optional[str]
    
    # For ranking task:
    ranking: Optional[List[int]]                 # indices best→worst, e.g. [2,0,4,1,3]
    quality_dimensions: Optional[List[str]]
    best_response_explanation: Optional[str]
```

## Observation Space

```python
class ModelJuryObservation(BaseModel):
    task_type: str
    scenario_id: str
    question: str
    responses: List[str]     # responses to evaluate (3 for hallucination, 4 CoT steps for reasoning, 5 for ranking)
    instructions: str
    step: int
    max_steps: int
    previous_feedback: Optional[str]
    chain_of_thought: Optional[List[str]]
```

## Reward Function

Dense partial reward — agents receive credit at multiple dimensions per episode:

**Hallucination task:**
- +0.5 for correct answer index
- +0.3 for explanation mentioning key false claim keywords
- +0.2 for substantive explanation (>30 chars)

**Reasoning task:**
- +0.4 for exact step identification (0.2 if off-by-one)
- +0.3 for correct error type classification
- +0.3 for explanation mentioning key concepts

**Ranking task:**
- +0.5 × Kendall tau correlation with expert ranking
- +0.3 for covering ground-truth quality dimensions
- +0.2 for best-response explanation mentioning key concepts

## Baseline Scores

Run with `Qwen/Qwen2.5-72B-Instruct` via HF Inference Router:

| Task | Score |
|------|-------|
| hallucination | ~0.72 |
| reasoning | ~0.61 |
| ranking | ~0.48 |
| **average** | **~0.60** |

## Setup

```bash
pip install openenv-core openai requests fastapi uvicorn pydantic
```

## Running Locally

```bash
# Start the server
cd server
uvicorn app.main:app --host 0.0.0.0 --port 7860

# In another terminal, run inference
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py
```

## Docker

```bash
docker build -t modeljury-env .
docker run -p 7860:7860 modeljury-env
```

## Deploying to Hugging Face Spaces

```bash
openenv push --repo-id your-username/modeljury-env
```

## Why This Environment Matters

Training agents to evaluate other models is a critical bottleneck in AI development:

1. **Scalable oversight**: Human annotation doesn't scale to billions of model outputs
2. **Automated red-teaming**: Agents that detect hallucinations can help filter training data  
3. **RLHF pipeline automation**: Replacing expensive human preference labels with trained evaluator agents
4. **Model improvement feedback loops**: The ranking task trains agents that can guide model improvement

This environment directly addresses the core challenge that Meta and Hugging Face face in building better LLMs.

## Submission hard-check checklist (real, no mockups)

This repository includes a validator script that runs the same gate checks expected in Round 1:

```bash
./scripts/validate-submission.sh https://your-space.hf.space
```

It verifies:

1. HF Space is live and `/reset` responds
2. `openenv.yaml` + root `inference.py` exist, and `openenv validate` (if installed)
3. Docker image builds and container responds on `/health`
4. All 3 tasks execute with deterministic graders and rewards in `[0.0, 1.0]`
5. Required inference env vars are configured (`API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`)

To run the validator locally:

```bash
chmod +x scripts/validate-submission.sh
./scripts/validate-submission.sh http://localhost:7860
```

Or against your live HF Space:

```bash
./scripts/validate-submission.sh https://huggingface.co/spaces/your-username/modeljury-env
```
