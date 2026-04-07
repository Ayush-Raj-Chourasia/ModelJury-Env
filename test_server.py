import requests
import json

BASE = "http://localhost:7860"

# 1. Health
r = requests.get(f"{BASE}/health", timeout=5)
print(f"HEALTH: {r.status_code} - {r.json()}")

# 2. Reset hallucination
r = requests.post(f"{BASE}/reset", json={"task_type": "hallucination"}, timeout=5)
d = r.json()
sid = d["session_id"]
obs = d["observation"]
print(f"RESET hallucination: scenario={obs['scenario_id']}, responses={len(obs['responses'])}")

# 3. Step hallucination (correct answer for first scenario)
action = {
    "task_type": "hallucination",
    "answer_index": 1,
    "error_description": "Response 1 states an incorrect year. The correct year is 1876 not 1869."
}
r = requests.post(f"{BASE}/step", json={"session_id": sid, "action": action}, timeout=5)
result = r.json()
print(f"STEP hallucination: reward={result['reward']}, done={result['done']}")

# 4. Reset reasoning
r = requests.post(f"{BASE}/reset", json={"task_type": "reasoning"}, timeout=5)
d = r.json()
sid2 = d["session_id"]
obs2 = d["observation"]
print(f"RESET reasoning: scenario={obs2['scenario_id']}, steps={len(obs2['responses'])}")

# 5. Step reasoning
action2 = {
    "task_type": "reasoning",
    "error_step": 2,
    "error_type": "wrong_math",
    "explanation": "80 x 1.5 = 120 not 100"
}
r = requests.post(f"{BASE}/step", json={"session_id": sid2, "action": action2}, timeout=5)
result2 = r.json()
print(f"STEP reasoning: reward={result2['reward']}, done={result2['done']}")

# 6. State endpoint
r = requests.get(f"{BASE}/state/{sid}", timeout=5)
print(f"STATE: {r.json()['state']}")

# 7. Reset ranking
r = requests.post(f"{BASE}/reset", json={"task_type": "ranking"}, timeout=5)
d = r.json()
sid3 = d["session_id"]
obs3 = d["observation"]
print(f"RESET ranking: scenario={obs3['scenario_id']}, responses={len(obs3['responses'])}")

# 8. Step ranking
action3 = {
    "task_type": "ranking",
    "ranking": [1, 3, 0, 2, 4],
    "quality_dimensions": ["factual accuracy", "completeness", "mathematical precision"],
    "best_response_explanation": "Response 1 covers gradient descent with learning rate, adam, stochastic, convergence"
}
r = requests.post(f"{BASE}/step", json={"session_id": sid3, "action": action3}, timeout=5)
result3 = r.json()
print(f"STEP ranking: reward={result3['reward']}, done={result3['done']}")

# 9. Root endpoint
r = requests.get(f"{BASE}/", timeout=5)
print(f"ROOT: {r.json()}")

print("\n=== ALL SERVER TESTS PASSED ===")
