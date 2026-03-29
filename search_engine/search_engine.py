import json
import re
from pathlib import Path

try:
    from nltk.stem import PorterStemmer
except ImportError:
    PorterStemmer = None


class _IdentityStemmer:
    def stem(self, word):
        return word


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

stemmer = PorterStemmer() if PorterStemmer else _IdentityStemmer()

with (DATA_DIR / "pages.json").open(encoding="utf-8") as f:
    pages = json.load(f)

with (DATA_DIR / "inverted_index.json").open(encoding="utf-8") as f:
    index = json.load(f)


def search(query):
    query = (query or "").strip()
    if not query:
        return []

    words = re.findall(r"\b\w+\b", query.lower())
    words = [stemmer.stem(word) for word in words]

    scores = {}

    for word in words:
        if word in index:
            for doc in index[word]:
                scores[doc] = scores.get(doc, 0) + 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results = []

    for doc_id, score in ranked[:10]:
        page = pages[doc_id]
        results.append(
            {
                "title": page["title"],
                "url": page["url"],
                "score": score,
            }
        )

    return results
