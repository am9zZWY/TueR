##### Parsing #####
from bs4 import BeautifulSoup
import requests
# Robots.txt
import urllib.robotparser

##### Threading #####
from concurrent.futures import ThreadPoolExecutor

# Maximum depth to crawl to
MAX_DEPTH = 5
# keywords = ["tübingen", "castle", "university", "museum", "food"]
# URL seeds to start crawling from
SEEDS = [
    "https://www.tuebingen.de/en/",
    # "https://en.wikipedia.org/wiki/Tübingen",
    # "https://www.komoot.com/guide/355570/castles-in-tuebingen-district",
    "https://www.unimuseum.uni-tuebingen.de/en/"
]


MAX_THREADS = 10

# List of links we have found
found_links = []


def get_domain(url: str) -> str:
    return "/".join(url.split("/")[0:3])


def can_fetch(url: str) -> bool:
    """
    Respect robots.txt and check if we can fetch a URL.
    For more information: http://www.robotstxt.org/robotstxt.html

    Parameters:
    - `url` (str): The URL to check.

    Returns:
    - `bool`: Whether we can fetch the URL or not.

    Example:
    ```python
    can_fetch("https://www.tuebingen.de/en/")
    ```
    """

    domain = get_domain(url)
    robots_url = domain + "/robots.txt"
    rp = urllib.robotparser.RobotFileParser(robots_url)
    try:
        rp.read()
    except:
        return True
    return rp.can_fetch("*", url)


def crawl(link: str, depth=0) -> None:
    """
    Crawls a website recursively and extracts links from HTML pages.

    Parameters:
    - `link` (str): The URL to start crawling from.
    - `depth` (int): The current depth of the crawl.

    Example:
    ```python
    crawl("https://www.tuebingen.de/en/")
    ```
    """

    # Stop if:
    # - reached the maximum depth, stop
    # - already found the link
    # - the link is not a valid URL
    if depth >= MAX_DEPTH or link in found_links or not link.startswith("http"):
        return

    # Check if we can fetch the URL
    if not can_fetch(link):
        return

    # Add the link to the list of links
    if link not in found_links:
        found_links.append(link)

    print(f"{' ' * depth}Crawling {link} ...")

    try:
        response = requests.get(link)

        soup = BeautifulSoup(response.text, "lxml")

        # Check for links
        for link in soup.find_all("a"):
            found_link = link.get("href")

            # If the link is not in the list of found links, crawl it
            if found_link not in found_links:
                if found_link.startswith("/"):
                    domain = get_domain(response.url)
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
