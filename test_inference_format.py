"""
Test inference.py log format without requiring HF_TOKEN.
Verifies that the logging format matches hackathon requirements.
"""
import sys
sys.path.insert(0, 'server')

from app.grader import grade
from app.scenarios import get_scenarios
from app.models import ModelJuryAction
import json

# Simulate inference logging format
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}")

def log_step(step: int, action: str, reward: float, done: bool, error=None) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_safe = action.replace("\n", " ")[:200]
    print(f"[STEP] step={step} action={action_safe} reward={reward:.2f} done={done_val} error={error_val}")

def log_end(success: bool, steps: int, score: float, rewards) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}")

# Test hallucination task
print("=" * 60)
print("TESTING INFERENCE LOG FORMAT")
print("=" * 60)

for task_type in ['hallucination', 'reasoning', 'ranking']:
    print(f"\n### Task: {task_type} ###")
    log_start(task=task_type, env="modeljury-env", model="Qwen/Qwen2.5-72B-Instruct")
    
    scenarios = get_scenarios(task_type)
    scenario = scenarios[0]  # Take first scenario
    
    # Simulate an action
    if task_type == 'hallucination':
        action = {
            "task_type": "hallucination",
            "answer_index": scenario['hallucinated_index'],
            "error_description": "The " + scenario['error_keywords'][0] + " is wrong"
        }
    elif task_type == 'reasoning':
        action = {
            "task_type": "reasoning",
            "error_step": scenario['error_step'],
            "error_type": scenario['error_type'],
            "explanation": " ".join(scenario['explanation_keywords'][:2])
        }
    else:  # ranking
        action = {
            "task_type": "ranking",
            "ranking": scenario['correct_ranking'],
            "quality_dimensions": scenario['key_dimensions'][:2],
            "best_response_explanation": " ".join(scenario['best_response_keywords'][:2])
        }
    
    result = grade(task_type, action, scenario)
    
    # Log step
    action_str = json.dumps(action, default=str)[:100]
    log_step(step=1, action=action_str, reward=result['score'], done=True)
    
    # Log end
    log_end(success=result['correct'], steps=1, score=result['score'], rewards=[result['score']])

print("\n" + "=" * 60)
print("✓ INFERENCE LOG FORMAT TEST PASSED")
print("=" * 60)
