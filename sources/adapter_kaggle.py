from __future__ import annotations

from typing import Dict, List

from sources.common import env, infer_formats, normalize_dataset
from sources.seed_datasets import SEED_DATASETS


SEARCH_BUCKETS = [
    "dataset",
    "image classification",
    "mental health csv",
    "traffic",
    "medical imaging",
]


def _kaggle_url(reference: str) -> str:
    return f"https://www.kaggle.com/datasets/{reference}"


def fetch_datasets(pages: int = 2, page_size: int = 20) -> List[dict]:
    username = env("KAGGLE_USERNAME")
    api_key = env("KAGGLE_KEY")
    if not username or not api_key:
        return [
            normalize_dataset("kaggle", dataset)
            for dataset in SEED_DATASETS
            if dataset["source"] == "kaggle"
        ]

    datasets: Dict[str, dict] = {}

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi  # type: ignore

        api = KaggleApi()
        api.authenticate()

        for bucket in SEARCH_BUCKETS:
            for page in range(1, pages + 1):
                for item in api.dataset_list(search=bucket, page=page, max_size=page_size):
                    reference = getattr(item, "ref", "") or ""
                    if not reference or "/" not in reference:
                        continue

                    datasets[reference] = normalize_dataset(
                        "kaggle",
                        {
                            "id": reference,
                            "title": getattr(item, "title", "") or reference.split("/")[-1].replace("-", " ").title(),
                            "description": getattr(item, "subtitle", "") or getattr(item, "description", ""),
                            "tags": [tag.name for tag in getattr(item, "tags", []) or [] if getattr(tag, "name", "")],
                            "url": _kaggle_url(reference),
                            "license": getattr(item, "licenseName", "") or "Unknown",
                            "formats": infer_formats(getattr(item, "subtitle", ""), getattr(item, "tags", [])),
                            "task_types": [],
                            "size": getattr(item, "totalBytes", "") or "Unknown",
                            "downloads": getattr(item, "downloadCount", 0) or 0,
                            "last_updated": str(getattr(item, "lastUpdated", "") or "")[:10],
                            "language": "Unknown",
                        },
                    )

        if datasets:
            return list(datasets.values())
    except Exception:
        pass

    return [
        normalize_dataset("kaggle", dataset)
        for dataset in SEED_DATASETS
        if dataset["source"] == "kaggle"
    ]
