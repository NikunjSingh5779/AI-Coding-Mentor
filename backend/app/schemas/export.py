"""
Export JSON Schema for frontend types generation.
"""

import json
from pathlib import Path
from app.schemas.snapshot import CodeSnapshot
from app.schemas.diagnostic import Diagnostic
from app.schemas.ws import WSEnvelope, FastAnalysisPayload


def export_schemas(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    schemas = {
        "CodeSnapshot": CodeSnapshot.model_json_schema(),
        "Diagnostic": Diagnostic.model_json_schema(),
        "WSEnvelope": WSEnvelope.model_json_schema(),
        "FastAnalysisPayload": FastAnalysisPayload.model_json_schema(),
    }

    for name, schema in schemas.items():
        with open(output_dir / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)


if __name__ == "__main__":
    export_schemas(Path(__file__).parent / "exported")
