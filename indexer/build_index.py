import json 
import re
from collections import defaultdict

with open("C:\\Projects\\Web Search Engine\\data\\pages.json","r") as f:
    pages=json.load(f)
index=defaultdict(list)

for doc_id,page in enumerate(pages):
    text=page['text'].lower()
    words=re.findall(r'\b\w+\b',text)
    unique_words=set(words)
    for word in unique_words: 
        index[word].append(doc_id)

with open("C:\\Projects\\Web Search Engine\\data\\inverted_index.json","w") as f:
    json.dump(index,f,indent=4)

print("Index built successfully.")
print("Total documents=",len(pages))
print("Total unique words in index=",len(index))
