import sys
import os

# Add 'server' to path so we can import 'app'
sys.path.insert(0, os.path.join(os.getcwd(), 'server'))

from app.grader import grade
from app.scenarios import get_scenarios

def test_ranges():
    tasks = ['hallucination', 'reasoning', 'ranking']
    all_pass = True
    
    for task in tasks:
        print(f"Testing {task}...")
        scenarios = get_scenarios(task)
        s = scenarios[0]
        
        # Test 1: Perfect score attempt
        if task == 'hallucination':
            action = {
                'answer_index': s['hallucinated_index'],
                'error_description': ' '.join(s['error_keywords']) + ' extra text to ensure it is substantive enough for the grader'
            }
        elif task == 'reasoning':
            action = {
                'error_step': s['error_step'],
                'error_type': s['error_type'],
                'explanation': ' '.join(s['explanation_keywords'])
            }
        else: # ranking
            action = {
                'ranking': s['correct_ranking'],
                'quality_dimensions': s['key_dimensions'],
                'best_response_explanation': ' '.join(s['best_response_keywords'])
            }
            
        res_perfect = grade(task, action, s)
        score_perfect = res_perfect['score']
        print(f"  Perfect action score: {score_perfect}")
        
        # Test 2: Absolute failure attempt
        if task == 'hallucination':
            action_fail = {'answer_index': -1, 'error_description': ''}
        elif task == 'reasoning':
            action_fail = {'error_step': -1, 'error_type': 'wrong', 'explanation': ''}
        else:
            action_fail = {'ranking': [], 'quality_dimensions': [], 'best_response_explanation': ''}
            
        res_fail = grade(task, action_fail, s)
        score_fail = res_fail['score']
        print(f"  Failed action score: {score_fail}")
        
        if not (0.0 < score_perfect < 1.0) or not (0.0 < score_fail < 1.0):
            print(f"  FAILED range check for {task}!")
            all_pass = False
        else:
            print(f"  PASSED range check for {task}.")
            
    if all_pass:
        print("\nSUCCESS: All scores are strictly between 0 and 1.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    test_ranges()
