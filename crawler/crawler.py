import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin 
import json
visited=set()
to_visit=[]

pages=[]


def crawl(url):
    if url in visited:
        return
    print("Crawling",url)
    try:
        headers={
            "User-Agent":"Mozilla/5.0"
        }
        response=requests.get(url,headers=headers,timeout=5)
    except:
        return
    visited.add(url)

    soup=BeautifulSoup(response.text,'html.parser')

    title=soup.title.string if soup.title else ""

    paragraphs=soup.find_all("p")

    text=" ".join(p.get_text() for p in paragraphs)

    pages.append({
        "url":url,
        "title":title,
        "text":text
    })

    links=soup.find_all("a")
    print("Links found:", len(links))


    for link in links:
        href=link.get("href")

        if href and not href.startswith('#') :
            full_url=urljoin(url,href)

            if full_url.startswith("https://en.wikipedia.org") and full_url not in visited and full_url not in to_visit:
                to_visit.append(full_url)
seed_url = "https://en.wikipedia.org/wiki/Search_engine"

to_visit.append(seed_url)


while to_visit and len(visited)<20:
    url=to_visit.pop(0)
    crawl(url)

with open("..\data\pages.json","w") as f:
    json.dump(pages,f,indent=4)
print("Finished crawling. Pages saved to pages.json")




  