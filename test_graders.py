"""Quick test: verify all graders and environment class work."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from app.grader import grade
from app.scenarios import get_scenarios
from app.env import ModelJuryEnvironment
from app.models import ModelJuryAction, ModelJuryObservation

print("=== GRADER TESTS ===")

# Hallucination
print("\n--- Hallucination ---")
for s in get_scenarios('hallucination'):
    desc = ' '.join(s['error_keywords']) + ' is factually wrong in this response'
    r = grade('hallucination', {'answer_index': s['hallucinated_index'], 'error_description': desc}, s)
    print(f"  {s['id']}: score={r['score']:.4f} correct={r['correct']}")
    assert 0.0 <= r['score'] <= 1.0, f"Score out of range: {r['score']}"

# Reasoning
print("\n--- Reasoning ---")
for s in get_scenarios('reasoning'):
    exp = ' '.join(s['explanation_keywords'])
    r = grade('reasoning', {'error_step': s['error_step'], 'error_type': s['error_type'], 'explanation': exp}, s)
    print(f"  {s['id']}: score={r['score']:.4f} correct={r['correct']}")
    assert 0.0 <= r['score'] <= 1.0, f"Score out of range: {r['score']}"

# Ranking
print("\n--- Ranking ---")
for s in get_scenarios('ranking'):
    exp = ' '.join(s['best_response_keywords'])
    r = grade('ranking', {'ranking': s['correct_ranking'], 'quality_dimensions': s['key_dimensions'], 'best_response_explanation': exp}, s)
    print(f"  {s['id']}: score={r['score']:.4f}")
    assert 0.0 <= r['score'] <= 1.0, f"Score out of range: {r['score']}"

# Zero-score tests
print("\n--- Zero-score tests ---")
r = grade('hallucination', {'answer_index': -1, 'error_description': ''}, get_scenarios('hallucination')[0])
print(f"  hallucination_wrong: score={r['score']:.4f}")
assert 0.0 <= r['score'] <= 1.0

r = grade('reasoning', {'error_step': -1, 'error_type': 'wrong', 'explanation': ''}, get_scenarios('reasoning')[0])
print(f"  reasoning_wrong: score={r['score']:.4f}")
assert 0.0 <= r['score'] <= 1.0

r = grade('ranking', {'ranking': [], 'quality_dimensions': [], 'best_response_explanation': ''}, get_scenarios('ranking')[0])
print(f"  ranking_wrong: score={r['score']:.4f}")
assert 0.0 <= r['score'] <= 1.0

print("\n=== ENVIRONMENT TESTS ===")
env = ModelJuryEnvironment()

# Test reset for each task type
for task in ['hallucination', 'reasoning', 'ranking']:
    obs = env.reset(task_type=task, seed=42)
    print(f"\n--- {task} reset ---")
    print(f"  question: {obs.question[:60]}...")
    print(f"  responses: {len(obs.responses)} items")
    print(f"  done: {obs.done}")
    print(f"  reward: {obs.reward}")
    assert obs.done == False
    assert obs.reward == 0.0

# Test step for hallucination
obs = env.reset(task_type='hallucination', seed=42)
action = ModelJuryAction(
    task_type='hallucination',
    answer_index=1,
    error_description='The year 1869 is wrong, the correct year is 1876'
)
obs = env.step(action)
print(f"\n--- hallucination step ---")
print(f"  done: {obs.done}")
print(f"  reward: {obs.reward}")
print(f"  score: {obs.score}")
print(f"  feedback: {obs.feedback}")
assert obs.done == True
assert 0.0 <= obs.reward <= 1.0

# Test state
state = env.state
print(f"\n--- state ---")
print(f"  episode_id: {state.episode_id}")
print(f"  step_count: {state.step_count}")

print("\n=== ALL TESTS PASSED ===")
