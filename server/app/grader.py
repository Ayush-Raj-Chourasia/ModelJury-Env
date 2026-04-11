"""
Grader module — all scoring is fully deterministic.
Ground truth is pre-defined in scenario data.
"""
from typing import Dict, Any



def clamp_score(score: float) -> float:
    """Ensure score falls strictly within (0, 1) per Phase 2 requirements."""
    # Enforce strictly between 0 and 1 (not 0.0 and not 1.0)
    return max(0.01, min(0.99, round(score, 4)))


def grade_hallucination(action: dict, ground_truth: dict) -> Dict[str, Any]:
    """
    Score hallucination detection task. Max = 1.0.

    Breakdown:
      0.5 — correct answer_index
      0.3 — error_description mentions key false claim keywords
      0.2 — error_description is substantive (>30 chars)
    """
    score = 0.0
    breakdown: Dict[str, float] = {}
    feedback_parts = []

    correct_idx = ground_truth["hallucinated_index"]
    if action.get("answer_index") == correct_idx:
        score += 0.5
        breakdown["correct_identification"] = 0.5
        feedback_parts.append("Correct response identified.")
    else:
        breakdown["correct_identification"] = 0.0
        feedback_parts.append(
            f"Wrong. Hallucinated response was index {correct_idx}."
        )

    desc = (action.get("error_description") or "").lower()
    keywords = [kw.lower() for kw in ground_truth.get("error_keywords", [])]
    hits = sum(1 for kw in keywords if kw in desc)
    kw_score = round(min(0.3, hits * 0.15), 3)
    score += kw_score
    breakdown["keyword_coverage"] = kw_score
    if hits:
        feedback_parts.append(f"Explanation mentioned {hits}/{len(keywords)} key error terms.")
    else:
        feedback_parts.append("Explanation missed the key false claims.")

    if len(desc) >= 30:
        score += 0.2
        breakdown["explanation_quality"] = 0.2
        feedback_parts.append("Explanation is substantive.")
    else:
        breakdown["explanation_quality"] = 0.0
        feedback_parts.append("Explanation too brief.")

    return {
        "score": clamp_score(score),
        "breakdown": breakdown,
        "feedback": " ".join(feedback_parts),
        "correct": action.get("answer_index") == correct_idx,
    }


def grade_reasoning_error(action: dict, ground_truth: dict) -> Dict[str, Any]:
    """
    Score reasoning trace task. Max = 1.0.

    Breakdown:
      0.4 — exact step identification (0.2 if one-off)
      0.3 — correct error_type classification
      0.3 — explanation mentions ground-truth keywords
    """
    score = 0.0
    breakdown: Dict[str, float] = {}
    feedback_parts = []

    correct_step = ground_truth["error_step"]
    agent_step = action.get("error_step")

    if agent_step == correct_step:
        score += 0.4
        breakdown["step_identification"] = 0.4
        feedback_parts.append(f"Correct — error is at step {correct_step}.")
    elif agent_step is not None and abs(int(agent_step) - int(correct_step)) == 1:
        score += 0.2
        breakdown["step_identification"] = 0.2
        feedback_parts.append(
            f"Close — off by one step. Error was step {correct_step}."
        )
    else:
        breakdown["step_identification"] = 0.0
        feedback_parts.append(f"Wrong step. Error was at step {correct_step}.")

    correct_type = ground_truth.get("error_type", "")
    if action.get("error_type") == correct_type:
        score += 0.3
        breakdown["error_type"] = 0.3
        feedback_parts.append("Correct error type.")
    else:
        breakdown["error_type"] = 0.0
        feedback_parts.append(f"Wrong error type. Was '{correct_type}'.")

    explanation = (action.get("explanation") or "").lower()
    keywords = [kw.lower() for kw in ground_truth.get("explanation_keywords", [])]
    hits = sum(1 for kw in keywords if kw in explanation)
    exp_score = round(min(0.3, hits * 0.1), 3)
    score += exp_score
    breakdown["explanation"] = exp_score
    feedback_parts.append(f"Explanation matched {hits}/{len(keywords)} key concepts.")

    return {
        "score": clamp_score(score),
        "breakdown": breakdown,
        "feedback": " ".join(feedback_parts),
        "correct": agent_step == correct_step,
    }


def _kendall_tau_normalized(ranking1: list, ranking2: list) -> float:
    """Normalized Kendall tau similarity in [0, 1]. 1.0 = perfect agreement."""
    n = len(ranking1)
    if n <= 1:
        return 1.0
    pos1 = {v: i for i, v in enumerate(ranking1)}
    pos2 = {v: i for i, v in enumerate(ranking2)}
    items = [x for x in ranking1 if x in pos2]
    concordant = discordant = 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            agree = (pos1[a] < pos1[b]) == (pos2[a] < pos2[b])
            if agree:
                concordant += 1
            else:
                discordant += 1
    total = concordant + discordant
    return concordant / total if total else 0.5


def grade_ranking(action: dict, ground_truth: dict) -> Dict[str, Any]:
    """
    Score comparative ranking task. Max = 1.0.

    Breakdown:
      0.5 — Kendall tau correlation with expert ranking
      0.3 — quality_dimensions cover ground-truth criteria
      0.2 — best_response_explanation mentions key concepts
    """
    score = 0.0
    breakdown: Dict[str, float] = {}
    feedback_parts = []

    gt_ranking = ground_truth["correct_ranking"]
    agent_ranking = action.get("ranking") or []

    if len(agent_ranking) == len(gt_ranking):
        tau = _kendall_tau_normalized(agent_ranking, gt_ranking)
        rank_score = round(tau * 0.5, 3)
        score += rank_score
        breakdown["ranking_correlation"] = rank_score
        feedback_parts.append(
            f"Ranking similarity (Kendall tau): {tau:.2f}."
        )
    else:
        breakdown["ranking_correlation"] = 0.0
        feedback_parts.append(
            f"Expected ranking of {len(gt_ranking)} items, got {len(agent_ranking)}."
        )

    agent_dims = [d.lower() for d in (action.get("quality_dimensions") or [])]
    correct_dims = [d.lower() for d in ground_truth.get("key_dimensions", [])]
    dim_hits = sum(
        1 for cd in correct_dims if any(cd in ad or ad in cd for ad in agent_dims)
    )
    dim_score = round(min(0.3, dim_hits * 0.1), 3)
    score += dim_score
    breakdown["dimension_coverage"] = dim_score
    feedback_parts.append(
        f"Dimension coverage: {dim_hits}/{len(correct_dims)} key criteria."
    )

    explanation = (action.get("best_response_explanation") or "").lower()
    kw_list = [kw.lower() for kw in ground_truth.get("best_response_keywords", [])]
    kw_hits = sum(1 for kw in kw_list if kw in explanation)
    exp_score = round(min(0.2, kw_hits * 0.07), 3)
    score += exp_score
    breakdown["explanation_quality"] = exp_score
    feedback_parts.append(
        f"Best-response explanation: {kw_hits}/{len(kw_list)} key concepts."
    )

    return {
        "score": clamp_score(score),
        "breakdown": breakdown,
        "feedback": " ".join(feedback_parts),
        "correct": (breakdown["ranking_correlation"] >= 0.35),
    }


def grade(task_type: str, action: dict, ground_truth: dict) -> Dict[str, Any]:
    """Dispatch to the correct grader."""
    if task_type == "hallucination":
        return grade_hallucination(action, ground_truth)
    elif task_type == "reasoning":
        return grade_reasoning_error(action, ground_truth)
    elif task_type == "ranking":
        return grade_ranking(action, ground_truth)
    else:
        raise ValueError(f"Unknown task_type: {task_type}")
