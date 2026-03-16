import json
import re
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()

with open("../data/pages.json") as f:
    pages = json.load(f)

with open("../data/inverted_index.json") as f:
    index = json.load(f)

def search(query):

    words = re.findall(r'\b\w+\b', query.lower())
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

        results.append({
            "title": page["title"],
            "url": page["url"],
            "score": score
        })

    return results