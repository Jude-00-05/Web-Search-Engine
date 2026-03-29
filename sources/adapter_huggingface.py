from __future__ import annotations

from typing import Dict, List

from sources.common import infer_formats, normalize_dataset
from sources.seed_datasets import SEED_DATASETS


SEARCH_BUCKETS = [None, "image", "text", "audio", "medical", "traffic", "tabular", "classification"]


def _format_title(dataset_id: str) -> str:
    name = dataset_id.split("/")[-1]
    return name.replace("_", " ").replace("-", " ").title()


def fetch_datasets(limit_per_bucket: int = 80) -> List[dict]:
    datasets: Dict[str, dict] = {}

    try:
        from huggingface_hub import HfApi  # type: ignore

        api = HfApi()
        for bucket in SEARCH_BUCKETS:
            kwargs = {
                "limit": limit_per_bucket,
                "full": True,
                "sort": "downloads",
                "direction": -1,
            }
            if bucket:
                kwargs["search"] = bucket

            for item in api.list_datasets(**kwargs):
                dataset_id = getattr(item, "id", "") or ""
                if not dataset_id:
                    continue

                card = getattr(item, "cardData", {}) or {}
                tags = list(getattr(item, "tags", []) or [])
                formats = infer_formats(tags, card.get("dataset_info"), card.get("configs"))
                url = f"https://huggingface.co/datasets/{dataset_id}"

                datasets[dataset_id] = normalize_dataset(
                    "huggingface",
                    {
                        "id": dataset_id,
                        "title": card.get("pretty_name") or _format_title(dataset_id),
                        "description": getattr(item, "description", "") or card.get("description", ""),
                        "tags": tags,
                        "url": url,
                        "license": card.get("license") or "Unknown",
                        "formats": formats or ["parquet"],
                        "task_types": card.get("task_categories") or [],
                        "downloads": getattr(item, "downloads", 0) or 0,
                        "last_updated": str(getattr(item, "lastModified", "") or "")[:10],
                        "language": (card.get("language") or ["Unknown"])[0]
                        if isinstance(card.get("language"), list)
                        else card.get("language"),
                    },
                )

        if datasets:
            return list(datasets.values())
    except Exception:
        pass

    return [
        normalize_dataset("huggingface", dataset)
        for dataset in SEED_DATASETS
        if dataset["source"] == "huggingface"
    ]
