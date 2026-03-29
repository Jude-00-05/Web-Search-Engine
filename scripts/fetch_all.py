from __future__ import annotations

import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sources.adapter_datagov import fetch_datasets as fetch_datagov
from sources.adapter_github import fetch_datasets as fetch_github
from sources.adapter_huggingface import fetch_datasets as fetch_huggingface
from sources.adapter_kaggle import fetch_datasets as fetch_kaggle
from sources.adapter_uci import fetch_datasets as fetch_uci
from sources.validation import validate_many

DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = DATA_DIR / "merged_datasets.json"
REPORT_PATH = DATA_DIR / "fetch_report.json"


def canonical_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def is_duplicate(candidate: dict, existing: dict) -> bool:
    if candidate["source"] == existing["source"] and candidate["id"] == existing["id"]:
        return True
    if candidate["url"] and candidate["url"] == existing["url"]:
        return True

    title_similarity = SequenceMatcher(
        None,
        canonical_title(candidate["title"]),
        canonical_title(existing["title"]),
    ).ratio()
    return title_similarity >= 0.92


def deduplicate(datasets: list[dict]) -> tuple[list[dict], int]:
    deduped = []
    duplicates_removed = 0
    for dataset in datasets:
        if any(is_duplicate(dataset, existing) for existing in deduped):
            duplicates_removed += 1
            continue
        deduped.append(dataset)
    return deduped, duplicates_removed


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    adapters = [
        ("huggingface", fetch_huggingface),
        ("uci", fetch_uci),
        ("kaggle", fetch_kaggle),
        ("datagov", fetch_datagov),
        ("github", fetch_github),
    ]

    merged = []
    source_report = {}

    for source_name, fetcher in adapters:
        try:
            raw_datasets = fetcher()
            validation_report = validate_many(raw_datasets)
            valid_datasets = validation_report["valid"]
            invalid_datasets = validation_report["invalid"]

            print(f"[{source_name}] raw fetched: {len(raw_datasets)}")
            print(f"[{source_name}] valid kept: {len(valid_datasets)}")
            print(f"[{source_name}] invalid removed: {len(invalid_datasets)}")
            if validation_report["invalid_reason_counts"]:
                print(f"[{source_name}] invalid reasons: {validation_report['invalid_reason_counts']}")

            source_report[source_name] = {
                "raw_fetched": len(raw_datasets),
                "valid_kept": len(valid_datasets),
                "invalid_removed": len(invalid_datasets),
                "invalid_reason_counts": validation_report["invalid_reason_counts"],
            }
            merged.extend(valid_datasets)
        except Exception as error:
            print(f"[{source_name}] skipped: {error}")
            source_report[source_name] = {
                "raw_fetched": 0,
                "valid_kept": 0,
                "invalid_removed": 0,
                "invalid_reason_counts": {"adapter_error": 1},
            }

    deduped, duplicates_removed = deduplicate(merged)
    deduped.sort(key=lambda item: (item["title"].lower(), item["source"]))

    source_counts = Counter(dataset["source"] for dataset in deduped)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(deduped, file, indent=2, ensure_ascii=False)

    report = {
        "sources": source_report,
        "duplicates_removed": duplicates_removed,
        "final_dataset_count": len(deduped),
        "final_source_counts": dict(source_counts),
    }
    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(f"[pipeline] duplicates removed: {duplicates_removed}")
    print(f"[pipeline] final valid datasets: {len(deduped)}")
    print(f"[pipeline] source counts: {dict(source_counts)}")
    print(f"[pipeline] saved merged datasets to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
