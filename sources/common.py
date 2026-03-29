from __future__ import annotations

import os
import re
from html import unescape
from html.parser import HTMLParser
from datetime import datetime
from typing import Any, Dict, Iterable, List
from urllib.parse import urlsplit, urlunsplit


NORMALIZED_FIELDS = [
    "id",
    "title",
    "description",
    "tags",
    "source",
    "url",
    "license",
    "formats",
    "task_types",
    "size",
    "downloads",
    "last_updated",
    "language",
]

GENERIC_URLS = {
    "https://github.com",
    "https://github.com/",
    "https://huggingface.co",
    "https://huggingface.co/",
    "https://huggingface.co/datasets",
    "https://huggingface.co/datasets/",
    "https://www.kaggle.com",
    "https://www.kaggle.com/",
    "https://www.kaggle.com/datasets",
    "https://www.kaggle.com/datasets/",
    "https://archive.ics.uci.edu",
    "https://archive.ics.uci.edu/",
    "https://catalog.data.gov",
    "https://catalog.data.gov/",
    "https://catalog.data.gov/dataset",
    "https://catalog.data.gov/dataset/",
}

DATASET_KEYWORDS = {
    "dataset",
    "datasets",
    "data",
    "corpus",
    "benchmark",
    "tabular",
    "csv",
    "json",
    "parquet",
    "tsv",
    "images",
    "image",
    "audio",
    "text",
    "traffic",
    "medical",
    "survey",
    "classification",
}

DATASET_FILE_HINTS = {
    "csv",
    "json",
    "jsonl",
    "parquet",
    "tsv",
    "zip",
    "sqlite",
    "arrow",
    "image",
    "images",
    "audio",
    "txt",
}

PLACEHOLDER_DESCRIPTIONS = {
    "",
    "unknown",
    "n/a",
    "none",
    "no description",
    "no description available",
    "dataset",
}


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.parts.append(unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.parts.append(unescape(f"&#{name};"))

    def get_text(self) -> str:
        return " ".join(self.parts)


def clean_list(values: Iterable[Any] | None) -> List[str]:
    if not values:
        return []

    cleaned: List[str] = []
    seen = set()
    for value in values:
        if value is None:
            continue
        item = str(value).strip()
        if not item:
            continue
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        cleaned.append(item)
    return cleaned


def clean_html_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    stripper = _HTMLStripper()
    try:
        stripper.feed(text)
        stripper.close()
        cleaned = stripper.get_text()
    except Exception:
        cleaned = re.sub(r"<[^>]+>", " ", text)

    cleaned = unescape(cleaned)
    cleaned = cleaned.replace("\xa0", " ")
    cleaned = re.sub(r"(?i)<br\s*/?>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def canonicalize_url(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""

    parts = urlsplit(raw)
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or parts.path

    if not netloc:
        return raw

    canonical = urlunsplit((scheme, netloc, path, "", ""))
    return canonical


def normalize_dataset(source: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow().strftime("%Y-%m-%d")
    normalized = {field: None for field in NORMALIZED_FIELDS}

    normalized["id"] = str(payload.get("id") or f"{source}-{payload.get('title', 'dataset')}")
    normalized["title"] = clean_html_text(payload.get("title") or "Untitled dataset")
    normalized["description"] = clean_html_text(payload.get("description") or "")
    normalized["tags"] = [clean_html_text(item) for item in clean_list(payload.get("tags"))]
    normalized["source"] = source
    normalized["url"] = canonicalize_url(str(payload.get("url") or ""))
    normalized["license"] = payload.get("license") or "Unknown"
    normalized["formats"] = [clean_html_text(item) for item in clean_list(payload.get("formats"))]
    normalized["task_types"] = [clean_html_text(item) for item in clean_list(payload.get("task_types"))]
    normalized["size"] = str(payload.get("size") or "Unknown").strip()
    normalized["downloads"] = int(payload.get("downloads") or 0)
    normalized["last_updated"] = str(payload.get("last_updated") or now)
    normalized["language"] = payload.get("language") or "Unknown"
    return normalized


def infer_formats(*values: Any) -> List[str]:
    inferred = []
    for value in values:
        if isinstance(value, (list, tuple, set)):
            tokens = [str(item).lower() for item in value]
        else:
            tokens = re.findall(r"[a-z0-9]+", str(value).lower())

        for token in tokens:
            if token in DATASET_FILE_HINTS and token not in inferred:
                inferred.append(token)

    return inferred


def description_is_meaningful(description: str) -> bool:
    text = str(description or "").strip()
    if not text:
        return False

    lowered = text.lower()
    if lowered in PLACEHOLDER_DESCRIPTIONS:
        return False

    words = re.findall(r"[a-z0-9]+", lowered)
    if len(words) < 5:
        return False

    return len(text) >= 24


def is_generic_homepage_url(url: str) -> bool:
    return canonicalize_url(url) in GENERIC_URLS


def is_valid_source_url(source: str, url: str) -> bool:
    canonical = canonicalize_url(url)
    if not canonical or is_generic_homepage_url(canonical):
        return False

    patterns = {
        "huggingface": r"^https://huggingface\.co/datasets/[^/]+(?:/[^/]+)?$",
        "kaggle": r"^https://www\.kaggle\.com/datasets/[^/]+/[^/]+$",
        "github": r"^https://github\.com/[^/]+/[^/]+$",
        "uci": r"^https://archive\.ics\.uci\.edu/dataset/\d+/[^/]+$",
        "datagov": r"^https://catalog\.data\.gov/dataset/[^/]+$",
    }
    pattern = patterns.get(source)
    if not pattern:
        return True
    return re.match(pattern, canonical) is not None


def github_dataset_signal_count(dataset: Dict[str, Any]) -> int:
    text_chunks = [
        dataset.get("title", ""),
        dataset.get("description", ""),
        " ".join(dataset.get("tags", [])),
        " ".join(dataset.get("task_types", [])),
    ]
    text = " ".join(str(chunk).lower() for chunk in text_chunks)
    signals = 0

    if any(keyword in text for keyword in DATASET_KEYWORDS):
        signals += 1
    if any(str(fmt).lower() in DATASET_FILE_HINTS for fmt in dataset.get("formats", [])):
        signals += 1
    if dataset.get("downloads", 0) >= 5:
        signals += 1

    return signals


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip() or default
