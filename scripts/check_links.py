from __future__ import annotations

import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sources.common import canonicalize_url, is_generic_homepage_url, is_valid_source_url

DATA_DIR = BASE_DIR / "data"
INPUT_PATH = DATA_DIR / "merged_datasets.json"
OUTPUT_PATH = DATA_DIR / "merged_datasets.json"
REPORT_PATH = DATA_DIR / "link_check_report.json"
MAX_WORKERS = 8
TIMEOUT_SECONDS = 8


def inspect_dataset_url(dataset: dict) -> Tuple[bool, dict]:
    url = dataset.get("url", "")
    try:
        request = Request(url, headers={"User-Agent": "DatasetSearchEngine/1.0"})
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            final_url = canonicalize_url(response.geturl())
            status_code = getattr(response, "status", 200)

        if status_code >= 400:
            return False, {"reason": "http_error", "status": status_code, "final_url": final_url}
        if is_generic_homepage_url(final_url):
            return False, {"reason": "redirected_to_homepage", "final_url": final_url}
        if not is_valid_source_url(dataset.get("source", ""), final_url):
            return False, {"reason": "redirected_to_invalid_detail_page", "final_url": final_url}

        return True, {"final_url": final_url}
    except HTTPError as error:
        return False, {"reason": "http_error", "status": error.code, "final_url": canonicalize_url(error.geturl() or url)}
    except URLError as error:
        return False, {"reason": "network_error", "error": str(error.reason), "final_url": canonicalize_url(url)}
    except Exception as error:
        return False, {"reason": "unexpected_error", "error": str(error), "final_url": canonicalize_url(url)}


def main() -> None:
    with INPUT_PATH.open(encoding="utf-8") as file:
        datasets = json.load(file)

    kept = []
    removed = []
    reason_counts = Counter()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(inspect_dataset_url, dataset): dataset for dataset in datasets}
        for future in as_completed(future_map):
            dataset = future_map[future]
            is_valid, details = future.result()

            if is_valid:
                dataset["url"] = details["final_url"]
                kept.append(dataset)
            else:
                reason_counts[details.get("reason", "unknown")] += 1
                removed.append({"dataset": dataset, "details": details})

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(sorted(kept, key=lambda item: item["title"].lower()), file, indent=2, ensure_ascii=False)

    report = {
        "checked": len(datasets),
        "kept": len(kept),
        "removed": len(removed),
        "removed_reason_counts": dict(reason_counts),
        "removed_items": removed,
    }
    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(f"Checked {len(datasets)} dataset links.")
    print(f"Kept {len(kept)} live dataset links.")
    print(f"Removed {len(removed)} dead or redirected links.")
    print(f"Removal reasons: {dict(reason_counts)}")


if __name__ == "__main__":
    main()
