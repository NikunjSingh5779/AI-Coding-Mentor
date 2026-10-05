"""
Evaluation metrics calculation (Precision, Recall, F1, Latency Percentiles).
"""

from typing import List, Dict, Any, Set


def calculate_classification_metrics(
    true_positives: int,
    false_positives: int,
    false_negatives: int
) -> Dict[str, float]:
    """Calculate precision, recall, and F1 score."""
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 1.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    """Calculate p50, p90, p95, p99 percentiles from a list of latencies."""
    if not values:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0, "max": 0.0}

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def _pct(p: float) -> float:
        idx = int(p * n)
        return sorted_vals[min(idx, n - 1)]

    return {
        "p50": round(_pct(0.50), 2),
        "p90": round(_pct(0.90), 2),
        "p95": round(_pct(0.95), 2),
        "p99": round(_pct(0.99), 2),
        "mean": round(sum(sorted_vals) / n, 2),
        "max": round(sorted_vals[-1], 2),
    }
