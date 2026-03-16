import json 
import re
from collections import defaultdict
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()
with open("..\\data\\pages.json","r") as f:
    pages=json.load(f)

with open ("..\\data\\stopwords.txt","r") as f:
    stopwords=set(word.lower() for word in f.read().splitlines())
    
index=defaultdict(list)

for doc_id, page in enumerate(pages):

    text = page["text"].lower()
    words = re.findall(r'\b\w+\b', text)
    for word in words:
        if word in stopwords:
            continue
        stemmed=stemmer.stem(word)
        if doc_id not in index[stemmed]:
            index[stemmed].append(doc_id)

with open("..\\data\\inverted_index.json","w") as f:
    json.dump(index,f,indent=4)

print("Index built successfully.")
print("Total documents=",len(pages))
print("Total unique words in index=",len(index))