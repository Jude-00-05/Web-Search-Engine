from __future__ import annotations

from typing import Dict, List

from sources.common import infer_formats, normalize_dataset
from sources.seed_datasets import SEED_DATASETS


def _dataset_detail_url(item: dict) -> str:
    dataset_id = item.get("uci_id") or item.get("id")
    slug = item.get("name") or item.get("slug") or ""
    normalized_slug = (
        str(slug)
        .strip()
        .lower()
        .replace(" ", "+")
        .replace("/", "+")
    )

    if dataset_id and normalized_slug:
        return f"https://archive.ics.uci.edu/dataset/{dataset_id}/{normalized_slug}"
    return str(item.get("url") or "")


def fetch_datasets() -> List[dict]:
    datasets: Dict[str, dict] = {}

    try:
        from ucimlrepo import list_available_datasets  # type: ignore

        catalog = list_available_datasets()
        for item in catalog:
            dataset_id = str(item.get("uci_id") or item.get("id") or "")
            if not dataset_id:
                continue

            datasets[dataset_id] = normalize_dataset(
                "uci",
                {
                    "id": dataset_id,
                    "title": item.get("name"),
                    "description": item.get("abstract") or item.get("summary"),
                    "tags": item.get("characteristics") or item.get("keywords"),
                    "url": _dataset_detail_url(item),
                    "license": item.get("license"),
                    "formats": infer_formats(item.get("file_formats"), item.get("characteristics"), "csv"),
                    "task_types": item.get("task"),
                    "size": item.get("instances"),
                    "last_updated": item.get("date_donated"),
                    "language": item.get("language"),
                },
            )

        if datasets:
            return list(datasets.values())
    except Exception:
        pass

    return [
        normalize_dataset("uci", dataset)
        for dataset in SEED_DATASETS
        if dataset["source"] == "uci"
    ]
