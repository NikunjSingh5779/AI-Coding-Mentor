"""
Evaluation Report Writer.
Writes JSON and Markdown evaluation reports to eval/reports/.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def save_report(report_data: Dict[str, Any], report_type: str = "eval") -> Path:
    """Save report in both JSON and Markdown format in eval/reports/."""
    reports_dir = Path(__file__).resolve().parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = reports_dir / f"{report_type}_{timestamp}.json"
    md_path = reports_dir / f"{report_type}_{timestamp}.md"

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Write Markdown
    md_lines = [
        f"# Evaluation Report: {report_type.upper()}",
        f"**Date:** {datetime.now().isoformat()}",
        "",
        "## Summary",
    ]

    for k, v in report_data.items():
        if isinstance(v, dict):
            md_lines.append(f"### {k}")
            for sub_k, sub_v in v.items():
                md_lines.append(f"- **{sub_k}:** {sub_v}")
        elif isinstance(v, list):
            md_lines.append(f"### {k} (Count: {len(v)})")
        else:
            md_lines.append(f"- **{k}:** {v}")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return json_path
