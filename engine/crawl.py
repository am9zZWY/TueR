##### General #####
import json
import os
import sys
##### Parsing #####
from bs4 import BeautifulSoup
import requests
# Robots.txt
import urllib.robotparser

##### Threading #####
from concurrent.futures import ThreadPoolExecutor

# Maximum size of the links
MAX_SIZE = 1000
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


def save_state():
    """
    Saves the global state to a file.
    """

    global ignore_links, found_links

    # Create directory for crawler states
    if not os.path.exists("crawler_states"):
        os.makedirs("crawler_states")

    with open(f"crawler_states/global.json", "w") as f:
        # Write it as json
        f.write(json.dumps({
            "ignore_links": list(ignore_links),
            "found_links": list(found_links)
        }))


def load_state():
    """
    Loads the global state from a file into memory.
    """

    global ignore_links, found_links

    if not os.path.exists(f"crawler_states/global.json"):
        print("No global state found")
        return

    with open(f"crawler_states/global.json", "r") as f:
        data = json.loads(f.read())
        ignore_links = set(data["ignore_links"])
        found_links = set(data["found_links"])


class Crawler:
    def __init__(self, identifier: str, start_link: str) -> None:
        self.identifier = identifier
        self.to_crawl = [start_link]
        self.visited_links = set()
        self.load_crawlers_state()

    def save_crawlers_state(self) -> None:
        """
        Saves the state of the crawler to a file.
        """

        # Create directory for crawler states
        if not os.path.exists("crawler_states"):
            os.makedirs("crawler_states")

        with open(f"crawler_states/crawler_state_{self.identifier}.json", "w") as f:
            # Write it as json
            f.write(json.dumps({
                "to_crawl": self.to_crawl,
                "visited_links": list(self.visited_links)
            }))

    def load_crawlers_state(self) -> None:
        """
        Loads the state of the crawler from a file into memory.
        """

        if not os.path.exists(f"crawler_states/crawler_state_{self.identifier}.txt"):
            print(f"No state found for crawler {self.identifier}")
            return [], []

        with open(f"crawler_states/crawler_state_{self.identifier}.json", "r") as f:
            data = json.loads(f.read())
            self.to_crawl = data["to_crawl"]
            self.visited_links = set(data["visited_links"])

    def crawl(self) -> None:
        """
        Crawls a website iteratively and extracts links from HTML pages.

        Example:
        ```python
        crawler = Crawler("0", "https://www.tuebingen.de/en/")
        ```
        """

        while self.to_crawl:
            # If we have reached the maximum size, stop
            if len(found_links) >= MAX_SIZE:
                print("max size reached")
                break

            # Get the link to crawl
            link = self.to_crawl.pop()

            print(f"Crawling {link}: ...", end="")

            if not link.startswith("http"):
                print("not a valid URL")
                continue

            if link in ignore_links or link in self.visited_links:
                print("already ignored or visited")
                continue

            # Check if we can fetch the URL
            if not can_fetch(link):
                print("robots.txt disallows")
                ignore_links.add(link)
                continue

            try:
                response = requests.get(link)
                soup = BeautifulSoup(response.text, "lxml")

                # Check language in html-tag and in the link
                html_lang = soup.find("html").get("lang")
                if (html_lang is not None and html_lang not in LANGS) and not any([lang in link for lang in LANGS]):
                    print("language not supported")
                    ignore_links.add(link)
                    continue

                text = soup.text.lower()
                # Check if there is any of the required keywords in the text
                if not any([keyword in text for keyword in REQUIRED_KEYWORDS]):
                    ignore_links.add(link)
                    print("no required keywords")
                    continue

                # Check for links
                for a_tag in soup.find_all("a", href=True):
                    found_link = a_tag.get("href")

                    # If the link is anchor, ignore it
                    if found_link.startswith("#"):
                        continue

                    if found_link.startswith("/"):
                        domain = get_domain(response.url)
                        found_link = domain + found_link

                    if found_link not in self.visited_links and found_link not in ignore_links:
                        self.to_crawl.append(found_link)

                # Add the link to the list of links
                if link not in found_links and link not in ignore_links:
                    found_links.add(link)
                    self.visited_links.add(link)

                print("done")
            except Exception as e:
                print("error occurred")
                # Do nothing if an error occurs
                continue


def main():
    crawlers = []
    load_state()

    try:
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            for i, seed in enumerate(SEEDS):
                crawler = Crawler(i, seed)
                crawlers.append(crawler)
                executor.submit(crawler.crawl)

        for crawler in crawlers:
            crawler.save_crawlers_state()

        print("Found", len(found_links), "links")
        for link in found_links:
            print(link)

    except KeyboardInterrupt:
        print('Interrupted')
        try:
            for crawler in crawlers:
                crawler.save_crawlers_state()
            save_state()
            sys.exit(130)
        except SystemExit:
            os._exit(130)


if __name__ == "__main__":
    main()
