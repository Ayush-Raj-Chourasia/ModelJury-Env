"""
inference.py — ModelJury-Env baseline inference script.

Runs an LLM agent against all three tasks and emits structured logs.

Log format (MUST NOT DEVIATE):
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...>

Usage:
  export HF_TOKEN=your_token
  export API_BASE_URL=https://router.huggingface.co/v1
  export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
  python inference.py
"""
import os
import json
import sys
import textwrap
from typing import List, Optional

import requests
from openai import OpenAI

# ── Configuration ──────────────────────────────────────────────────────────────
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK = "modeljury-env"
MAX_STEPS = 1
TEMPERATURE = 0.1
MAX_TOKENS = 800
SUCCESS_SCORE_THRESHOLD = 0.4

if API_KEY is None:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

# ── Logging helpers (exact format required) ────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_safe = action.replace("\n", " ")[:200]
    print(
        f"[STEP] step={step} action={action_safe} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ── Environment HTTP helpers ───────────────────────────────────────────────────

def env_reset(task_type: str) -> dict:
    """Reset the environment for a given task type via HTTP."""
    resp = requests.post(
        f"{ENV_BASE_URL}/reset",
        json={"task_type": task_type},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_step(action: dict) -> dict:
    """Take a step in the environment via HTTP."""
    resp = requests.post(
        f"{ENV_BASE_URL}/step",
        json={"action": action},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ── System prompts per task ────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "hallucination": textwrap.dedent("""
        You are an expert AI evaluator. You will be shown a factual question and three LLM-generated responses.
        Exactly ONE response contains a factual error (hallucination).

        You MUST respond with a JSON object — no other text, no markdown:
        {
          "task_type": "hallucination",
          "answer_index": <0, 1, or 2>,
          "error_description": "<specific false claim and why it is wrong>"
        }
    """).strip(),

    "reasoning": textwrap.dedent("""
        You are an expert at analyzing chain-of-thought reasoning.
        You will be shown a math or logic problem and an LLM's step-by-step solution.
        Exactly ONE step contains an error.

        Error types: wrong_math, invalid_inference, wrong_fact, missing_info

        You MUST respond with a JSON object — no other text, no markdown:
        {
          "task_type": "reasoning",
          "error_step": <step number, 1-indexed>,
          "error_type": "<wrong_math|invalid_inference|wrong_fact|missing_info>",
          "explanation": "<what is wrong and what the correct value/reasoning should be>"
        }
    """).strip(),

    "ranking": textwrap.dedent("""
        You are an expert LLM evaluator. You will be shown a question and 5 LLM responses (indexed 0-4).
        Rank all 5 from best to worst quality.

        You MUST respond with a JSON object — no other text, no markdown:
        {
          "task_type": "ranking",
          "ranking": [<best_index>, ..., <worst_index>],
          "quality_dimensions": ["<criterion1>", "<criterion2>", ...],
          "best_response_explanation": "<why your top-ranked response is the best>"
        }
    """).strip(),
}


def build_user_prompt(observation: dict) -> str:
    """Build user prompt from observation data."""
    task_type = observation.get("task_type", "")
    question = observation.get("question", "")
    instructions = observation.get("instructions", "")
    responses = observation.get("responses", [])

    parts = [f"Instructions: {instructions}", f"\nQuestion: {question}"]

    if task_type in ("hallucination", "ranking"):
        parts.append("\nResponses:")
        for i, r in enumerate(responses):
            parts.append(f"[{i}] {r}")
    elif task_type == "reasoning":
        parts.append("\nChain-of-thought solution:")
        for step in responses:
            parts.append(f"  {step}")

    return "\n".join(parts)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call the LLM and return response text."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content.strip()


def parse_action(raw: str, task_type: str) -> dict:
    """Parse LLM output into action dict, with fallback."""
    # Strip markdown fences
    clean = raw.replace("```json", "").replace("```", "").strip()
    try:
        obj = json.loads(clean)
        obj["task_type"] = task_type  # ensure task_type is set
        return obj
    except json.JSONDecodeError:
        # Fallback safe action
        if task_type == "hallucination":
            return {"task_type": task_type, "answer_index": 0, "error_description": raw[:200]}
        elif task_type == "reasoning":
            return {"task_type": task_type, "error_step": 1, "error_type": "wrong_math", "explanation": raw[:200]}
        else:
            return {"task_type": task_type, "ranking": [0, 1, 2, 3, 4],
                    "quality_dimensions": ["accuracy"], "best_response_explanation": raw[:200]}


# ── Task runner ────────────────────────────────────────────────────────────────

def run_task(task_type: str) -> float:
    """Run one complete episode for the given task. Returns final score."""
    log_start(task=task_type, env=BENCHMARK, model=MODEL_NAME)
    rewards: List[float] = []
    final_score = 0.0
    step_num = 0

    try:
        # Reset
        reset_data = env_reset(task_type)
        observation = reset_data.get("observation", reset_data)

        for step_num in range(1, MAX_STEPS + 1):
            user_prompt = build_user_prompt(observation)
            system_prompt = SYSTEM_PROMPTS[task_type]

            raw_response = call_llm(system_prompt, user_prompt)
            action = parse_action(raw_response, task_type)
            action_str = json.dumps(action, separators=(",", ":"))

            try:
                result = env_step(action)

                # Handle both flat and nested response formats
                obs_data = result.get("observation", result)
                reward = result.get("reward", obs_data.get("reward", 0.0))
                done = result.get("done", obs_data.get("done", True))
                error = obs_data.get("last_action_error") or result.get("error")

                if reward is None:
                    reward = obs_data.get("score", 0.0) or 0.0

                final_score = reward
                rewards.append(reward)
                log_step(step=step_num, action=action_str, reward=reward, done=done, error=error)

                observation = obs_data
                if done:
                    break

            except Exception as e:
                log_step(step=step_num, action=action_str, reward=0.0, done=True, error=str(e))
                rewards.append(0.0)
                break

    except Exception as e:
        log_step(step=step_num or 1, action="null", reward=0.0, done=True, error=str(e))
        if not rewards:
            rewards.append(0.0)

    finally:
        # [END] must ALWAYS be emitted, even on exception
        success = final_score >= SUCCESS_SCORE_THRESHOLD
        log_end(success=success, steps=len(rewards), score=final_score, rewards=rewards)

    return final_score


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    tasks = ["hallucination", "reasoning", "ranking"]
    scores = {}
    for task in tasks:
        scores[task] = run_task(task)

    # Summary line
    avg = sum(scores.values()) / len(scores)
    print(f"\n=== ModelJury-Env Summary ===", flush=True)
    for task, score in scores.items():
        print(f"  {task:20s}: {score:.3f}", flush=True)
    print(f"  {'average':20s}: {avg:.3f}", flush=True)


if __name__ == "__main__":
    main()
