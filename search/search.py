import json 
import re

with open("C:\\Projects\\Web Search Engine\\data\\pages.json","r") as f:
    pages=json.load(f)
with open("C:\\Projects\\Web Search Engine\\data\\inverted_index.json","r") as f:
    index=json.load(f)

def search(query):
    query=query.lower()
    words=re.findall(r'\b\w+\b',query)
    results=set()
    for word in words:
        if word in index:
            docs=index[word]
            results.update(docs)
        
    return results

while True:
    query=input("Enter search query (or 'exit' to quit): ")
    if query.lower()=='exit':
        break
    docs=search(query)
    if not docs:
        print("No results found.")
        continue
    print("Results:\n ")

    for doc_id in docs:
        page=pages[doc_id]
        print(f"Title: {page['title']}")
        print(f"URL: {page['url']}")
        print()
    