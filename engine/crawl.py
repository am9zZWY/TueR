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
    "https://www.bio.mpg.de/2923/en",
    "https://www.uni-tuebingen.de/en/",
    "https://www.my-stuwe.de/en/",
    "https://www.unimuseum.uni-tuebingen.de/en/",
    "https://www.komoot.com/guide/210692/attractions-around-tuebingen",
    "https://hoelderlinturm.de/english/",
    "https://www.stocherkahnfahrten.com/English/Stocherkahnrennen-English.html",
    "https://www.germany.travel/en/cities-culture/tuebingen.html",
    "https://justinpluslauren.com/things-to-do-in-tubingen-germany/",

]
LANGS = ["en", "en-GB", "en-US", "english"]

MAX_THREADS = 10

# List of links we have found
ignore_links = set()
found_links = set()


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
    print(f"{' ' * depth}Crawling {link} ...", end="")
    
    if not link.startswith("http"):
        print("not a valid URL")
        return
    
    if link in ignore_links:
        print("already ignored")
        return

    # Check if we can fetch the URL
    if not can_fetch(link):
        print("robots.txt disallows")
        ignore_links.add(link)
        return

    try:
        response = requests.get(link)

        soup = BeautifulSoup(response.text, "lxml")

        # Check language in html-tag and in the link
        html_lang = soup.find("html").get("lang")
        if (html_lang is not None and html_lang not in LANGS) and not any([lang in link for lang in LANGS]):
            print("language not supported")
            ignore_links.add(link)
            return

        # Add the link to the list of links
        if link not in found_links and link not in ignore_links:
            found_links.add(link)

        text = soup.text.lower()
        # Check if there is any of the required keywords in the text
        if not any([keyword in text for keyword in REQUIRED_KEYWORDS]):
            ignore_links.add(link)
            return

        # Check for links
        for link in soup.find_all("a", href=True):
            found_link = link.get("href")

            # If the link is anchor, ignore it
            if found_link.startswith("#"):
                continue

            # If the link is not in the list of found links, crawl it
            if found_link not in found_links:
                if found_link.startswith("/"):
                    domain = get_domain(response.url)
                    found_link = domain + found_link
                
                if depth >= MAX_DEPTH:
                    print(f"reached max depth of {MAX_DEPTH}")
                    return

                crawl(found_link, depth + 1)
    except Exception as e:
        print("error occurred: " + str(e))
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
