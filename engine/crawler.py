# Parsing
from bs4 import BeautifulSoup
import requests
# Threading
from concurrent.futures import ThreadPoolExecutor

# Maximum depth to crawl to
MAX_DEPTH = 5
# keywords = ["tübingen", "castle", "university", "museum", "food"]
# URL seeds to start crawling from
SEEDS = [
    "https://www.tuebingen.de/en/",
    #"https://en.wikipedia.org/wiki/Tübingen",
    #"https://www.komoot.com/guide/355570/castles-in-tuebingen-district",
    "https://www.unimuseum.uni-tuebingen.de/en/"
]


MAX_THREADS = 10

# List of links we have found
found_links = []


def crawl(link, depth=0):
    # If we have reached the maximum depth, stop
    if depth >= MAX_DEPTH:
        return

    # Add the link to the list of links
    if link not in found_links:
        found_links.append(link)

    print('\r', f"Crawling {link} at depth {depth}", end="")

    try:
        response = requests.get(link)

        soup = BeautifulSoup(response.text, "lxml")

        # Check for links
        for link in soup.find_all("a"):
            found_link = link.get("href")
            
            # If the link is not in the list of found links, crawl it
            if found_link not in found_links:
                if found_link.startswith("/"):
                    domain = "/".join(response.url.split("/")[0:3])
                    found_link = domain + found_link

                crawl(found_link, depth + 1)
    except:
        # Do nothing if an error occurs
        pass


def main():
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(crawl, seed) for seed in SEEDS]
        for future in futures:
            future.result()

    print("Found", len(found_links), "links")
    for link in found_links:
        print(link)


if __name__ == "__main__":
    main()
