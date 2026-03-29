from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple

from sources.common import (
    description_is_meaningful,
    github_dataset_signal_count,
    is_generic_homepage_url,
    is_valid_source_url,
    normalize_dataset,
)


def validate_dataset(dataset: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
    normalized = normalize_dataset(dataset.get("source", "unknown"), dataset)
    reasons: List[str] = []

    if not normalized["title"] or normalized["title"].lower() == "untitled dataset":
        reasons.append("missing_title")
    if not normalized["url"]:
        reasons.append("missing_url")
    elif is_generic_homepage_url(normalized["url"]):
        reasons.append("generic_homepage_url")
    elif not is_valid_source_url(normalized["source"], normalized["url"]):
        reasons.append("invalid_source_url")

    if not description_is_meaningful(normalized["description"]):
        reasons.append("weak_description")

    if normalized["source"] == "github" and github_dataset_signal_count(normalized) < 2:
        reasons.append("weak_github_dataset_signal")

    return len(reasons) == 0, normalized, reasons


def validate_many(datasets: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    valid: List[Dict[str, Any]] = []
    invalid: List[Dict[str, Any]] = []
    reasons = Counter()
    source_counts = Counter()

    for dataset in datasets:
        is_valid, cleaned, dataset_reasons = validate_dataset(dataset)
        source_counts[cleaned["source"]] += 1

        if is_valid:
            valid.append(cleaned)
            continue

        invalid.append({"dataset": cleaned, "reasons": dataset_reasons})
        reasons.update(dataset_reasons)

    return {
        "valid": valid,
        "invalid": invalid,
        "invalid_reason_counts": dict(reasons),
        "source_counts": dict(source_counts),
    }
