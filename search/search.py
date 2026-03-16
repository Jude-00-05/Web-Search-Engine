import json 
import re
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()
with open("../data/pages.json","r") as f:
    pages=json.load(f)
with open("../data/inverted_index.json","r") as f:
    index=json.load(f)
with open("..\\data\\stopwords.txt","r") as f:
    stopwords=set(f.read().splitlines())

def search(query):
    query=query.lower()
    words=re.findall(r'\b\w+\b',query)
    words=[stemmer.stem(word) for word in words]
    words=[word for word in words if word not in stopwords]
    scores={}
    for word in words:
        if word in index:
            docs=index[word]
            for doc in docs:
                scores[doc] = scores.get(doc, 0) + 1
    ranked=sorted(scores.items(),key=lambda x:x[1],reverse=True)
    return ranked

while True:
    query=input("Enter search query (or 'exit' to quit): ")
    if query.lower()=='exit':
        break
    docs=search(query)
    if not docs:
        print("No results found.")
        continue
    print("Results:\n ")

    for doc_id,score in docs:
        page=pages[doc_id]
        print(f"Title: {page['title']}")
        print(f"URL: {page['url']}")
        print(f"Score: {score}")
        print()
    