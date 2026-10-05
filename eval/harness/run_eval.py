"""
Evaluation Runner for Fast Static Analysis.
Evaluates precision, recall, and accuracy across dataset cases.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend and eval directories to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
eval_dir = root_dir / "eval"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(eval_dir) not in sys.path:
    sys.path.insert(0, str(eval_dir))

from app.analysis.pipeline import AnalysisPipeline
from harness.metrics import calculate_classification_metrics
from harness.report import save_report


async def run_analysis_evaluation() -> dict:
    dataset_dir = eval_dir / "datasets" / "code_bugs" / "python"
    cases = list(dataset_dir.glob("*.json"))

    if not cases:
        print("No evaluation cases found in dataset directory.")
        return {}

    pipeline = AnalysisPipeline()

    tp = 0
    fp = 0
    fn = 0
    clean_correct = 0
    total_clean = 0
    case_results = []

    print(f"Running analysis evaluation on {len(cases)} cases...")

    for case_file in cases:
        with open(case_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        code_file = case_file.with_suffix(".py")
        code = ""
        if code_file.exists():
            with open(code_file, "r", encoding="utf-8") as f:
                code = f.read()

        is_clean = metadata.get("is_clean", False)
        expected_cats = set(metadata.get("expected_categories", []))

        diags, timings = await pipeline.analyze(code)
        detected_cats = {d.category for d in diags}

        passed = False
        if is_clean:
            total_clean += 1
            if len(diags) == 0:
                clean_correct += 1
                passed = True
            else:
                fp += 1
        else:
            # Check if expected categories were detected
            overlap = expected_cats.intersection(detected_cats)
            if overlap:
                tp += 1
                passed = True
            else:
                fn += 1

        case_results.append({
            "id": metadata.get("id"),
            "is_clean": is_clean,
            "passed": passed,
            "expected": list(expected_cats),
            "detected": list(detected_cats),
            "diagnostics_count": len(diags),
        })

    metrics = calculate_classification_metrics(tp, fp, fn)
    clean_acc = clean_correct / total_clean if total_clean > 0 else 1.0

    print("\n--- Analysis Evaluation Results ---")
    print(f"  Precision: {metrics['precision']}")
    print(f"  Recall:    {metrics['recall']}")
    print(f"  F1 Score:  {metrics['f1']}")
    print(f"  Clean Accuracy: {round(clean_acc, 4)} ({clean_correct}/{total_clean})")

    report_data = {
        "suite": "fast_static_analysis",
        "total_cases": len(cases),
        "metrics": metrics,
        "clean_accuracy": round(clean_acc, 4),
        "case_results": case_results,
    }

    report_path = save_report(report_data, "analysis_eval")
    print(f"\nReport saved to {report_path}")
    return report_data


def main():
    asyncio.run(run_analysis_evaluation())


if __name__ == "__main__":
    main()
