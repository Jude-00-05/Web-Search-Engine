from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.build_index import main as build_index
from scripts.check_links import main as check_links
from scripts.fetch_all import main as fetch_all
from scripts.validate_datasets import main as validate_datasets


def main() -> None:
    print("[rebuild] fetching datasets")
    fetch_all()
    print("[rebuild] validating merged datasets")
    validate_datasets()
    print("[rebuild] checking dataset links")
    check_links()
    print("[rebuild] building search index")
    build_index()
    print("[rebuild] pipeline complete")


if __name__ == "__main__":
    main()
