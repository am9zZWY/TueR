##### General #####
import collections  # For deque
import json
import os
import sys
##### Parsing #####
from bs4 import BeautifulSoup  # HTML parsing
import requests  # HTTP requests
from urllib.parse import urlparse  # Parsing URLs
# Robots.txt
import urllib.robotparser  # For checking robots.txt
##### Threading #####
from concurrent.futures import ThreadPoolExecutor
##### Tokenization #####
from custom_tokenizer import tokenize_data, tf_idf_vectorize, top_30_words
##### Language detection #####
from nltk.classify import textcat
##### Database #####
import duckdb

##### Constants #####
# Maximum size of the links
MAX_SIZE = 1000
# Keywords to search for
# They must be present in the HTML of the page
REQUIRED_KEYWORDS = ["tübingen", "tuebingen", "tubingen", "t%C3%BCbingen"]
# URL seeds to start crawling from
SEEDS = [
    "https://www.tuebingen.de/en/",
    "https://www.bio.mpg.de/2923/en",
    "https://www.uni-tuebingen.de/en/",
    "http://www.tuepedia.de",
    "https://health-nlp.com/index.html",
    "https://www.medizin.uni-tuebingen.de/en-de/startseite/",
    "https://www.my-stuwe.de/en/",
    "https://www.unimuseum.uni-tuebingen.de/en/",
    "https://www.komoot.com/guide/210692/attractions-around-tuebingen",
    "https://hoelderlinturm.de/english/",
    "https://www.fsi.uni-tuebingen.de/en/",
    "https://www.stocherkahnfahrten.com/English/Stocherkahnrennen-English.html",
    "https://www.germany.travel/en/cities-culture/tuebingen.html",
    "https://justinpluslauren.com/things-to-do-in-tubingen-germany/",
    "https://www.yelp.de/search?find_desc=&find_loc=Tübingen%2C+Baden-Württemberg",
    "https://www.tripadvisor.com/Tourism-g198539-Tubingen_Baden_Wurttemberg-Vacations.html",
]
# Domains to ignore
IGNORE_DOMAINS = [
    "github.com",
    "linkedin.com",
    "xing.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "youtube.com",
    "de.wikipedia.org",
    "wikipedia.org",
    "google.com",
    "google.de",
    "google.co.uk",
    "amazon.com",
    "cctue.de",
    "spotify.com",
]
# Supported languages
LANGS = ["en", "eng", "en-GB", "en-US", "english"]
# Maximum number of threads
MAX_THREADS = 10
# User-Agent
USER_AGENT = "Modern Search Engines University of Tuebingen Project Crawler (https://uni-tuebingen.de/de/262377)" 


def get_domain(url: str) -> str:
    """
    Extracts the domain from a URL.

    Parameters:
    - `url` (str): The URL to extract the domain from.

    Returns:
    - `str`: The domain of the URL.
    """

    return urlparse(url).netloc


def get_base_url(url: str) -> str:
    """
    Extracts the base URL from a URL.

    Parameters:
    - `url` (str): The URL to extract the base URL from.

    Returns:
    - `str`: The base URL of the URL.
    """

    return urlparse(url).scheme + "://" + urlparse(url).netloc


def check_robots(url: str) -> bool:
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

    domain = get_base_url(url)
    robots_url = domain + "/robots.txt"
    rp = urllib.robotparser.RobotFileParser(robots_url)
    try:
        rp.read()
    except:
        return True
    return rp.can_fetch("*", url)


def get_lang(text: str) -> str:
    """
    Extracts the language from a text.

    Parameters:
    - `text` (str): The text to extract the language from.

    Returns:
    - `str`: The language of the text.

    Example:
    ```python
    get_lang("Hello, world!")
    ```
    """

    tc = textcat.TextCat()
    return tc.guess_language(text)

# List of links we have found
ignore_links = set()
found_links = set()
to_crawl = collections.deque(SEEDS)
to_crawl_set = set(SEEDS)



class Crawler:
    def __init__(self, identifier: str, dbcon: duckdb.DuckDBPyConnection) -> None:
        self.identifier = identifier
        self.cursor = dbcon.cursor()
        print(f"Initialized Crawler {self.identifier}")

    def __del__(self) -> None:
        self.cursor.close()

    def crawl(self) -> None:
        """
        Crawls a website iteratively and extracts links from HTML pages.

        Example:
        ```python
        to_crawl = collections.deque(["https://www.tuebingen.de/en/"])
        crawler = Crawler("0")
        ```
        """

        global found_links, ignore_links, to_crawl
        i = 1

        while True:
            # If we have reached the maximum size, stop
            if len(found_links) >= MAX_SIZE:
                print("max size reached")
                break

            # Get the next link to crawl
            link = to_crawl.popleft()
            to_crawl_set.remove(link)

            crawling_str = f"Crawler {self.identifier} crawling {link}: "

            if not link.startswith("http"):
                print(crawling_str + "skipped")
                continue

            # Check if the domain is in the ignore list
            if any([domain in link for domain in IGNORE_DOMAINS]):
                print(crawling_str + "domain in ignore list")
                ignore_links.add(link)
                continue

            if link in ignore_links or link in found_links:
                print(crawling_str + "already ignored or visited")
                continue

            # Check if we can fetch the URL
            if not check_robots(link):
                print(crawling_str + "robots.txt disallows")
                ignore_links.add(link)
                continue

            try:
                response = requests.get(link, timeout=5, headers={"User-Agent": USER_AGENT}, allow_redirects=True, stream=True, proxies=False, auth=False, cookies=False)
                soup = BeautifulSoup(response.text, "lxml")
                text = soup.text.lower()

                # Check language in html-tag and in the link
                def check_lang(lang):
                    """
                    Check if the language is supported.
                    """
                    print("\tchecking lang")
                    return lang is not None and lang in LANGS
            
                def check_text_lang(text):
                    """
                    Check if the language of the text is supported.
                    """
                    print("\tchecking text lang")
                    tc = textcat.TextCat()
                    return check_lang(tc.guess_language(text))
                
                def check_link_lang(link):
                    """
                    Check if the language of the link is supported.
                    """
                    print("\tchecking link lang")
                    return any([split == lang for split in link.split("/") for lang in LANGS])
                    
                html_lang = soup.find("html").get("lang")
                xml_lang = soup.find("html").get("xml:lang")
                
                img_tags = soup.findAll("img")
                desciption = soup.find("meta", attrs={"name": "description"})
                desciption_content = desciption.get("content") if desciption is not None else ""
                title = soup.find("title")
                title_content = title.string if title is not None else ""

                text = soup.text.lower()
                alt_texts = [img.get("alt") for img in img_tags]
                text = text + " ".join(alt_texts) + " " + str(desciption_content) + " " + str(title_content)
                if i == 1:
                    print(f"Text: {text}")
                    print(f"Type of text: {type(text)}")
                    print("Now printing top 30 words")
                    top_30 = top_30_words(data=[text])
                    print(f"Top 30 words: {top_30}")
                    i+=1
            
                if not check_lang(html_lang) and not check_lang(xml_lang) and not check_link_lang(link) and not check_text_lang(text):
                    print(crawling_str + "unsupported language")
                    ignore_links.add(link)
                    continue

                # Check if there is any of the required keywords in the text
                if not any([keyword in text for keyword in REQUIRED_KEYWORDS]):
                    ignore_links.add(link)
                    print(crawling_str + "no required keywords")
                    continue

                # Check for links
                for a_tag in soup.find_all("a", href=True):
                    found_link = a_tag.get("href")

                    # If the link is anchor, ignore it
                    if found_link.startswith("#"):
                        continue

                    # TODO: Edge-case: If the link starts with ./
                    if found_link.startswith("/"):
                        base_url = get_base_url(response.url)
                        found_link = base_url + found_link

                    if found_link not in ignore_links and found_link not in found_links and found_link not in to_crawl_set and link.startswith("http"):
                        to_crawl.append(found_link)
                        to_crawl_set.add(found_link)

                # Add the link to the list of links
                if link not in found_links and link not in ignore_links:
                    found_links.add(link)

                print(crawling_str + "done")
            
            except Exception as e:
                print(crawling_str + "error occurred", e)
                # Do nothing if an error occurs
                continue


def save_state():
    """
    Saves the global state to a file.
    """

    global ignore_links, found_links, to_crawl

    # Create directory for crawler states
    if not os.path.exists("crawler_states"):
        os.makedirs("crawler_states")

    with open(f"crawler_states/global.json", "w") as f:
        # Write it as json
        f.write(json.dumps({
            "to_crawl": list(to_crawl),
            "ignore_links": list(ignore_links),
            "found_links": list(found_links),
        }))


def load_state():
    """
    Loads the global state from a file into memory.
    """

    global ignore_links, found_links, to_crawl, to_crawl_set

    if not os.path.exists(f"crawler_states/global.json"):
        print("No global state found")
        to_crawl = collections.deque(SEEDS)
        return

    with open(f"crawler_states/global.json", "r") as f:
        data = json.loads(f.read())
        to_crawl = collections.deque(data["to_crawl"])
        to_crawl_set = set(data["to_crawl"])
        ignore_links = set(data["ignore_links"])
        found_links = set(data["found_links"])


def start_crawl():
    load_state()

    crawlers = []
    con = duckdb.connect("crawlies.db")
    try:
        con.install_extension("fts")
        con.load_extension("fts")
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            for i in range(MAX_THREADS):
                crawler = Crawler(i, con)
                crawlers.append(crawler)
                executor.submit(crawler.crawl)

        con.close()
        save_state()

        print("Found", len(found_links), "links")
        for link in found_links:
            print(link)

    except KeyboardInterrupt:
        try:
            save_state()
            con.close()
            sys.exit(130)
        except SystemExit:
            con.close()
            os._exit(130)
    except Exception as e:
        con.close()


if __name__ == "__main__":
    start_crawl()
