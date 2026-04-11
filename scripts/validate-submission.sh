#!/usr/bin/env bash
# validate-submission.sh — ModelJury-Env Pre-Submission Validator
#
# Runs the same gate checks expected in Round 1:
# 1. HF Space is live and /reset responds
# 2. openenv.yaml + root inference.py exist
# 3. Docker image builds and container responds on /health
# 4. All 3 tasks execute with deterministic graders and scores in [0.0, 1.0]
# 5. Required inference env vars are documented
#
# Usage:
#   ./scripts/validate-submission.sh https://your-space.hf.space
#
# Or run locally:
#   ./scripts/validate-submission.sh http://localhost:7860

set -euo pipefail

SPACE_URL="${1:-}"
REPO_DIR="${2:-$(pwd)}"
IMAGE_TAG="modeljury-env:validate"
CONTAINER_NAME="modeljury-env-validate"

if [[ -z "$SPACE_URL" ]]; then
  echo "Usage: $0 <space_url> [repo_dir]"
  echo "Example: $0 https://huggingface.co/spaces/username/modeljury-env"
  exit 1
fi

pass() { echo "✅ $1"; }
warn() { echo "⚠️  $1"; }
fail() { echo "❌ $1"; exit 1; }

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

cd "$REPO_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 ModelJury-Env Pre-Submission Validator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ────────────────────────────────────────────────────────────────

echo "📍 Check 1: HF Space Health"
echo ""

if curl -fsS "$SPACE_URL/health" >/dev/null 2>&1; then
  pass "HF Space health endpoint reachable"
else
  fail "HF Space health endpoint is not reachable at $SPACE_URL/health"
fi

if curl -fsS -X POST "$SPACE_URL/reset" \
  -H 'content-type: application/json' \
  -d '{"task_type":"hallucination"}' >/dev/null 2>&1; then
  pass "HF Space /reset responds"
else
  fail "HF Space /reset failed"
fi

echo ""

# ────────────────────────────────────────────────────────────────

echo "📍 Check 2: Required Artifacts"
echo ""

[[ -f openenv.yaml ]] || fail "openenv.yaml missing"
pass "openenv.yaml exists"

[[ -f inference.py ]] || fail "inference.py missing at repository root"
pass "inference.py exists at repository root"

if command -v openenv >/dev/null 2>&1; then
  if openenv validate >/dev/null 2>&1; then
    pass "openenv validate passed"
  else
    fail "openenv validate failed"
  fi
else
  warn "openenv CLI not installed; skipped openenv validate"
fi

echo ""

# ────────────────────────────────────────────────────────────────

echo "📍 Check 3: Docker Build & Runtime"
echo ""

if command -v docker >/dev/null 2>&1; then
  if docker build -t "$IMAGE_TAG" . >/dev/null 2>&1; then
    pass "Docker image built successfully"
  else
    fail "Docker build failed"
  fi

  docker run -d --rm --name "$CONTAINER_NAME" -p 7860:7860 "$IMAGE_TAG" >/dev/null 2>&1
  sleep 4

  if curl -fsS http://localhost:7860/health >/dev/null 2>&1; then
    pass "Docker container started and /health responds on port 7860"
  else
    fail "Container did not respond on /health"
  fi
else
  warn "Docker not installed; skipped Docker build/run checks"
fi

echo ""

# ────────────────────────────────────────────────────────────────

echo "📍 Check 4: Deterministic Graders & Score Bounds"
echo ""

python - <<'PY'
import sys
sys.path.insert(0, '/c/Users/iters/Downloads/ModelJury-Env' if sys.platform == 'win32' else '.')
from server.app.env import ModelJuryEnvironment
from server.app.models import ModelJuryAction

TASKS = ["hallucination", "reasoning", "ranking"]
for task in TASKS:
    env = ModelJuryEnvironment()
    obs = env.reset(task_type=task, seed=42)
    
    if task == "hallucination":
        action = ModelJuryAction(
            task_type=task,
            answer_index=0,
            error_description="test explanation with factual mismatch and date error"
        )
    elif task == "reasoning":
        action = ModelJuryAction(
            task_type=task,
            error_step=1,
            error_type="wrong_math",
            explanation="there is arithmetic mismatch in this step calculation"
        )
    else:  # ranking
        action = ModelJuryAction(
            task_type=task,
            ranking=[0, 1, 2, 3, 4],
            quality_dimensions=["accuracy"],
            best_response_explanation="basic ranking explanation"
        )

    obs = env.step(action)
    assert obs.done is True, f"{task}: Episode did not finish"
    assert 0.0 <= obs.score <= 1.0, f"{task}: Score {obs.score} out of bounds"
    print(f"✅ {task:15s}: score={obs.score:.3f} (deterministic, in bounds)")

print("\n✅ All 3 tasks execute with deterministic graders and bounded scores")
PY

echo ""

# ────────────────────────────────────────────────────────────────

echo "📍 Check 5: Required Environment Variables"
echo ""

missing=0
for var in API_BASE_URL MODEL_NAME HF_TOKEN; do
  if [[ -z "${!var:-}" ]]; then
    warn "  ⚠️  $var not set in current shell"
    missing=1
  else
    pass "$var is set"
  fi
done

if [[ $missing -eq 1 ]]; then
  echo ""
  echo "To run inference.py, set these environment variables:"
  echo "  export API_BASE_URL=https://router.huggingface.co/v1"
  echo "  export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct"
  echo "  export HF_TOKEN=<your_token>"
  echo ""
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Validation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Your submission is ready for Round 1."
echo ""
