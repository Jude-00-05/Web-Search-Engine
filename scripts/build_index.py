from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    from nltk.stem import PorterStemmer
except ImportError:
    PorterStemmer = None


class _IdentityStemmer:
    def stem(self, word: str) -> str:
        return word


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sources.common import normalize_dataset

DATA_DIR = BASE_DIR / "data"
DATASETS_PATH = DATA_DIR / "merged_datasets.json"
STOPWORDS_PATH = DATA_DIR / "stopwords.txt"
OUTPUT_PATH = DATA_DIR / "inverted_index.json"
REPORT_PATH = DATA_DIR / "index_report.json"
SEARCH_FIELDS = ["title", "description", "tags", "task_types", "formats"]

stemmer = PorterStemmer() if PorterStemmer else _IdentityStemmer()


def load_stopwords() -> set[str]:
    with STOPWORDS_PATH.open(encoding="utf-8") as file:
        return {line.strip().lower() for line in file if line.strip()}


def tokenize(value: str, stopwords: set[str]) -> list[str]:
    tokens = re.findall(r"\b[a-z0-9]+\b", value.lower())
    return [stemmer.stem(token) for token in tokens if token not in stopwords]


def main() -> None:
    stopwords = load_stopwords()
    with DATASETS_PATH.open(encoding="utf-8") as file:
        datasets = [normalize_dataset(item.get("source", "unknown"), item) for item in json.load(file)]

    index = defaultdict(lambda: {field: {} for field in SEARCH_FIELDS})

    for doc_id, dataset in enumerate(datasets):
        for field in SEARCH_FIELDS:
            raw_value = dataset.get(field, "")
            text = " ".join(raw_value) if isinstance(raw_value, list) else str(raw_value)
            tokens = tokenize(text, stopwords)
            field_counts = defaultdict(int)
            for token in tokens:
                field_counts[token] += 1
            for token, count in field_counts.items():
                index[token][field][str(doc_id)] = count

    payload = {
        "metadata": {
            "document_count": len(datasets),
            "search_fields": SEARCH_FIELDS,
        },
        "terms": index,
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    report = {
        "indexed_datasets": len(datasets),
        "indexed_terms": len(index),
        "search_fields": SEARCH_FIELDS,
    }
    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(f"[index] final indexed datasets: {len(datasets)}")
    print(f"[index] indexed terms: {len(index)}")
    print(f"[index] saved index to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
