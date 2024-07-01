##### Parsing #####
from bs4 import BeautifulSoup
import requests
# Robots.txt
import urllib.robotparser

##### Threading #####
from concurrent.futures import ThreadPoolExecutor

# Maximum depth to crawl to
MAX_DEPTH = 5
# Keywords to search for
# They must be present in the HTML of the page
REQUIRED_KEYWORDS = ["tübingen", "tuebingen"]
# URL seeds to start crawling from
SEEDS = [
    "https://www.tuebingen.de/en/",
    # "https://en.wikipedia.org/wiki/Tübingen",
    "https://www.komoot.com/guide/355570/castles-in-tuebingen-district",
    "https://www.unimuseum.uni-tuebingen.de/en/",
    "https://www.tuebingen-info.de",
    "https://www.uni-tuebingen.de",
    "https://www.tuebingen.de",
    "https://www.tripadvisor.com/Tourism-g198539-Tubingen_Baden_Wurttemberg-Vacations.html",
    "https://www.lonelyplanet.com/germany/baden-wurttemberg/tubingen",
    "https://www.tuebingen-info.de/en",
    "https://www.my-stuwe.de/en/tuebingen/",
    "https://www.tuebingen-info.de/en/experience/shopping/farmers-market",
    "https://www.my-stuwe.de/en/",
    "https://www.swtue.de/en/",
    "https://en.wikipedia.org/wiki/T%C3%BCbingen",
    "https://www.tuebingen.de/en/calendar",
    "https://www.tuebingen-info.de/en/experience/nature",
    "https://www.ub.uni-tuebingen.de/en/",
    "https://www.tuebingen.de/en/7695.html",
    "https://www.tripadvisor.com/Attractions-g198539-Activities-c20-Tubingen_Baden_Wurttemberg.html",
    "https://www.kulturhalle-tuebingen.de",
    "https://www.tuebingen-info.de/en/experience/nature/hiking-cycling",
    "https://www.tagblatt.de",
    "https://www.kunsthalle-tuebingen.de",
    "https://www.meetup.com/topics/language-exchange/de/t%C3%BCbingen/",
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
    # - the link is not a valid URL
    # - already found the link
    if depth >= MAX_DEPTH or not link.startswith("http") or link in found_links:
        return

    # Check if we can fetch the URL
    if not can_fetch(link):
        return

    # Add the link to the list of links
    if link not in found_links:
        found_links.append(link)

    try:
        response = requests.get(link)

        soup = BeautifulSoup(response.text, "lxml")
        
        # Check language in html-tag
        if not "en" in soup.html["lang"]:
            return
        
        text = soup.text.lower()
        # Check for keywords
        if not any([keyword in text for keyword in REQUIRED_KEYWORDS]):
            return
        
        print(f"{' ' * depth}Crawling {link} ...")

        # Check for links
        for link in soup.find_all("a", href=True):
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
