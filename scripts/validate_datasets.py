from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sources.validation import validate_many

DATA_DIR = BASE_DIR / "data"
INPUT_PATH = DATA_DIR / "merged_datasets.json"
OUTPUT_PATH = DATA_DIR / "merged_datasets.json"
REPORT_PATH = DATA_DIR / "validation_report.json"


def main() -> None:
    with INPUT_PATH.open(encoding="utf-8") as file:
        datasets = json.load(file)

    report = validate_many(datasets)
    valid = report["valid"]

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(valid, file, indent=2, ensure_ascii=False)

    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(f"Validated {len(datasets)} datasets.")
    print(f"Kept {len(valid)} valid datasets.")
    print(f"Removed {len(report['invalid'])} invalid datasets.")
    print(f"Invalid reasons: {report['invalid_reason_counts']}")


if __name__ == "__main__":
    main()
