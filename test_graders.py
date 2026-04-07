import sys
sys.path.insert(0, 'server')
from app.grader import grade
from app.scenarios import get_scenarios

print('=== HALLUCINATION ===')
for s in get_scenarios('hallucination'):
    desc = 'The ' + s['error_keywords'][0] + ' is factually wrong in this response'
    r = grade('hallucination', {'task_type': 'hallucination', 'answer_index': s['hallucinated_index'], 'error_description': desc}, s)
    print(f"  {s['id']}: correct={r['correct']}, score={r['score']}")

print('=== REASONING ===')
for s in get_scenarios('reasoning'):
    exp = ' '.join(s['explanation_keywords'][:3])
    r = grade('reasoning', {'task_type': 'reasoning', 'error_step': s['error_step'], 'error_type': s['error_type'], 'explanation': exp}, s)
    print(f"  {s['id']}: correct={r['correct']}, score={r['score']}")

print('=== RANKING ===')
for s in get_scenarios('ranking'):
    exp = ' '.join(s['best_response_keywords'])
    r = grade('ranking', {'task_type': 'ranking', 'ranking': s['correct_ranking'], 'quality_dimensions': s['key_dimensions'][:3], 'best_response_explanation': exp}, s)
    print(f"  {s['id']}: score={r['score']}")

print('\nALL GRADER TESTS PASSED')
