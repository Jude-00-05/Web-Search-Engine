from __future__ import annotations

import json
from typing import Dict, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sources.common import infer_formats, normalize_dataset
from sources.seed_datasets import SEED_DATASETS


SEARCH_BUCKETS = ["dataset", "transport", "health", "traffic", "air quality"]


def _canonical_dataset_url(item: dict) -> str:
    slug = str(item.get("name") or "").strip()
    if slug:
        return f"https://catalog.data.gov/dataset/{slug}"
    return ""


def fetch_datasets(rows: int = 50, pages: int = 2) -> List[dict]:
    datasets: Dict[str, dict] = {}

    try:
        for bucket in SEARCH_BUCKETS:
            for page in range(pages):
                params = urlencode({"q": bucket, "rows": rows, "start": page * rows})
                request = Request(
                    f"https://catalog.data.gov/api/3/action/package_search?{params}",
                    headers={"User-Agent": "DatasetSearchEngine/1.0"},
                )
                with urlopen(request, timeout=10) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                for item in payload.get("result", {}).get("results", []):
                    dataset_id = str(item.get("id") or "")
                    if not dataset_id:
                        continue

                    datasets[dataset_id] = normalize_dataset(
                        "datagov",
                        {
                            "id": dataset_id,
                            "title": item.get("title"),
                            "description": item.get("notes"),
                            "tags": [tag.get("display_name") for tag in item.get("tags", [])],
                            "url": _canonical_dataset_url(item),
                            "license": item.get("license_title"),
                            "formats": infer_formats(
                                [resource.get("format") for resource in item.get("resources", [])],
                                item.get("title"),
                                item.get("notes"),
                            ),
                            "task_types": ["analysis", "open-data"],
                            "downloads": 0,
                            "last_updated": str(item.get("metadata_modified", ""))[:10],
                            "language": "English",
                        },
                    )

        if datasets:
            return list(datasets.values())
    except Exception:
        pass

    return [
        normalize_dataset("datagov", dataset)
        for dataset in SEED_DATASETS
        if dataset["source"] == "datagov"
    ]
