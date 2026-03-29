from __future__ import annotations

import json
from typing import Dict, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sources.common import DATASET_KEYWORDS, env, infer_formats, normalize_dataset
from sources.seed_datasets import SEED_DATASETS


SEARCH_BUCKETS = [
    "dataset in:name,description topics:dataset",
    "corpus in:name,description",
    "benchmark in:name,description",
    "csv data in:readme,description",
]
DATASET_EXTENSIONS = (".csv", ".json", ".jsonl", ".parquet", ".tsv", ".zip", ".txt")


def _request_json(url: str, token: str) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "DatasetSearchEngine/1.0",
        },
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _has_dataset_signal(item: dict, token: str) -> bool:
    text = " ".join(
        [
            str(item.get("name") or "").lower(),
            str(item.get("description") or "").lower(),
            " ".join(item.get("topics", []) or []).lower(),
        ]
    )
    keyword_signal = any(keyword in text for keyword in DATASET_KEYWORDS)
    star_signal = int(item.get("stargazers_count") or 0) >= 5

    file_signal = False
    try:
        contents_url = item.get("contents_url", "").replace("{+path}", "")
        if contents_url:
            contents = _request_json(contents_url, token)
            file_names = [str(entry.get("name") or "").lower() for entry in contents if isinstance(entry, dict)]
            file_signal = any(name.endswith(DATASET_EXTENSIONS) for name in file_names)
    except Exception:
        file_signal = False

    return (keyword_signal and star_signal) or file_signal


def fetch_datasets(per_page: int = 30, pages: int = 2) -> List[dict]:
    token = env("GITHUB_TOKEN")
    if not token:
        return [
            normalize_dataset("github", dataset)
            for dataset in SEED_DATASETS
            if dataset["source"] == "github"
        ]

    datasets: Dict[str, dict] = {}

    try:
        for bucket in SEARCH_BUCKETS:
            for page in range(1, pages + 1):
                params = urlencode({"q": bucket, "per_page": per_page, "page": page})
                payload = _request_json(f"https://api.github.com/search/repositories?{params}", token)

                for item in payload.get("items", []):
                    full_name = str(item.get("full_name") or "")
                    if not full_name or not _has_dataset_signal(item, token):
                        continue

                    datasets[full_name] = normalize_dataset(
                        "github",
                        {
                            "id": full_name,
                            "title": item.get("name"),
                            "description": item.get("description"),
                            "tags": item.get("topics"),
                            "url": item.get("html_url"),
                            "license": (item.get("license") or {}).get("spdx_id"),
                            "formats": infer_formats(item.get("topics"), item.get("description")),
                            "task_types": ["dataset", "repository"],
                            "downloads": item.get("stargazers_count"),
                            "last_updated": str(item.get("updated_at", ""))[:10],
                            "language": item.get("language"),
                        },
                    )

        if datasets:
            return list(datasets.values())
    except Exception:
        pass

    return [
        normalize_dataset("github", dataset)
        for dataset in SEED_DATASETS
        if dataset["source"] == "github"
    ]
