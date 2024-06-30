from bs4 import BeautifulSoup
import requests

max_depth = 2
seeds = [
    "https://en.wikipedia.org/wiki/Tübingen"
]
do_print = True

def crawl(link, depth=0):
    # If link is None or depth is greater than max_depth, return
    if link is None or depth >= max_depth or not link.startswith("https"):
        return
    
    if do_print:
        print("Crawling", link, "at depth", depth)

    try:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "html.parser")
        return [crawl(link.get("href"), depth + 1) for link in soup.find_all("a")]
    except:
        return []

for seed in seeds:
    print(crawl(seed))