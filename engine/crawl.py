##### General #####
import asyncio
import collections  # For deque
import json
import os
import sys
##### Parsing #####
from bs4 import BeautifulSoup  # HTML parsing
from aiohttp import ClientSession
from utils import check_robots, get_base_url
import requests  # HTTP requests
##### Threading #####
from pipeline import PipelineElement
from concurrent.futures import ThreadPoolExecutor
##### Tokenization #####
from custom_tokenizer import tokenize_data, tf_idf_vectorize, top_30_words
##### Language detection #####
from eld import LanguageDetector
##### Database #####
import duckdb
from custom_db import *

# Constants
# URL seeds to start crawling from
SEEDS = [
    # Official
    "https://www.tuebingen.de/en/",
    # University
    "https://www.uni-tuebingen.de/en/",
    "https://www.bio.mpg.de/2923/en",
    "https://health-nlp.com/index.html",
    "https://www.medizin.uni-tuebingen.de/en-de/startseite/",
    "https://www.my-stuwe.de/en/",
    "https://www.unimuseum.uni-tuebingen.de/en/",
    "https://www.fsi.uni-tuebingen.de/en/",
    "https://studieren.de/international-business-eberhard-karls-universitaet-tuebingen.studienprofil.t-0.a-68.c-110.html",
    "https://www.hih-tuebingen.de/en/?no_cache=1"
    # Events
    "https://www.dai-tuebingen.de/en/",
    "https://pintofscience.de/events/tuebingen",
    "http://www.tuepedia.de",
    "https://hoelderlinturm.de/english/",
    "https://www.tuebingen.de/en/leisure-tourism/culture/museums-galleries.html",
    "https://www.eventbrite.com/ttd/germany--tübingen/",
    # Tourism
    "https://www.komoot.com/guide/210692/attractions-around-tuebingen",
    "https://www.stocherkahnfahrten.com/English/Stocherkahnrennen-English.html",
    "https://www.germany.travel/en/cities-culture/tuebingen.html",
    "https://justinpluslauren.com/things-to-do-in-tubingen-germany/",
    "https://www.yelp.de/search?find_desc=&find_loc=Tübingen%2C+Baden-Württemberg",
    "https://www.tripadvisor.com/Tourism-g198539-Tubingen_Baden_Wurttemberg-Vacations.html",
]
# Language detector
LANG_DETECTOR = LanguageDetector()
# Ignore errors
SILENT_ERRORS = False


def log_error(error_msg):
    """
    Prints an error message if SILENT_ERRORS is False.
    Args:
        error_msg: The error message to print.

    Returns:

    """
    if not SILENT_ERRORS:
        logging.error(error_msg)


class Crawler(PipelineElement):
    def __init__(self, dbcon: duckdb.DuckDBPyConnection):
        super().__init__("Crawler")

        # Initialize the duckdb connection
        self.cursor = dbcon.cursor()

        # Initialize the crawler state
        self.urls_crawled = set()
        self.ignore_links = set()
        self.to_crawl_queue = collections.deque(SEEDS)
        self.to_crawl_set = set(self.to_crawl_queue)
        self._page_count = 0

        # Load the global state
        self._load_state()

        # Crawler configuration
        self.timeout = 10  # Timeout in seconds
        self.max_retries = 3  # Maximum number of retries
        self.retry_delay = 1  # Delay between retries in seconds
        self.max_size = 1000  # Maximum number of pages to crawl
        self.no_dynamic_content = False  # Disable dynamic content handling (Playwright)
        self.ignore_domains = ["github.com", "linkedin.com", "xing.com", "instagram.com", "twitter.com", "youtube.com",
                               "de.wikipedia.org", "wikipedia.org", "google.com", "google.de", "google.co.uk",
                               "pinterest.com", "amazon.com", "cctue.de", "spotify.com"]
        self.langs = ["en", "en-de", "eng", "en-GB", "en-US", "english"]
        self.required_keywords = ["tübingen", "tuebingen", "tubingen", "t%C3%BCbingen"]
        self.user_agents = [
            "University of Tuebingen Student Web Crawler Project (https://uni-tuebingen.de/de/262377; contact: "
            "webmaster@uni-tuebingen.de)",
            "Mozilla/5.0 (compatible; TuebingenUniBot/1.0; +https://uni-tuebingen.de/de/262377)",
            "Tuebingen University Research Crawler/1.0 (+https://uni-tuebingen.de/de/262377; Academic purposes only)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
            "Safari/537.36 (Tuebingen University Web Crawling Project)"
        ]
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def __del__(self) -> None:
        self.cursor.close()

        # Internal state
        self._page_count = 0

    @property
    def user_agent(self):
        # Cycle through user agents
        return self.user_agents[self._page_count % len(self.user_agents)]

    async def process(self):
        connector = TCPConnector(limit=100, force_close=True, enable_cleanup_closed=True)
        async with ClientSession(connector=connector, trust_env=True) as session:
            while not self.is_shutdown() and self.to_crawl_queue and len(self.urls_crawled) < self.max_size:
                tasks = []
                for _ in range(min(10, len(self.to_crawl_queue))):
                    if self.to_crawl_queue and len(self.urls_crawled) < self.max_size:
                        url = self.to_crawl_queue.popleft()
                        task = asyncio.create_task(self._process_url(session, url))
                        tasks.append(task)
                    else:
                        break

                if not tasks:
                    break

                # Wait for all tasks to complete or for shutdown
                completed, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                for task in completed:
                    try:
                        await task
                    except Exception as e:
                        log_error(f"Unhandled exception in task: {e}")

                if self.is_shutdown():
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
                    self.save_state()
                    break

                # If there are still pending tasks, add them back to the queue
                for task in pending:
                    url = task.get_coro().cr_frame.f_locals.get('url')
                    if url:
                        self.to_crawl_queue.appendleft(url)
                    task.cancel()

        logging.info("Crawler finished processing")

    async def _process_url(self, session, url: str):
        """
        Crawls a URL and processes the content.
        Args:
            session:
            url:

        Returns:

        """
        if len(self.urls_crawled) >= self.max_size:
            logging.info("Maximum size reached")
            return

        if not url.startswith("http"):
            logging.info(f"Invalid URL: {url}")
            return

        if any(domain in url for domain in self.ignore_domains):
            logging.info(f"Ignoring {url} because it is in the ignore domains list")
            self.ignore_links.add(url)
            return

        if url in self.ignore_links or url in self.urls_crawled:
            logging.info(f"Ignoring {url} because it is in the ignore or found list")
            return

        if not check_robots(url):
            logging.info(f"Ignoring {url} because it is disallowed by robots.txt")
            self.ignore_links.add(url)
            return

        html_content = await self._fetch(session, url)
        if html_content is None:
            logging.info(f"Error fetching {url}")
            self.ignore_links.add(url)
            return

        try:
            soup = BeautifulSoup(html_content, "lxml")
            text = soup.get_text().lower()
        except Exception as e:
            log_error(f"Error parsing {url}: {e}")
            self.ignore_links.add(url)
            return

        if not text or not soup:
            logging.info(f"Ignoring {url} because it is empty")
            self.ignore_links.add(url)
            return

        check_html_tag_lang = soup.find("html").get("lang") in self.langs
        check_xml_tag_lang = soup.find("html").get("xml:lang") in self.langs
        check_link_lang = any(split == lang for split in url.split("/") for lang in self.langs)
        check_text_lang = LANG_DETECTOR.detect(text) in self.langs

        if not check_html_tag_lang and not check_xml_tag_lang and not check_link_lang and not check_text_lang:
            logging.info(f"Ignoring {url} because it is not in the correct language")
            self.ignore_links.add(url)
            return

        if not any(keyword in text for keyword in self.required_keywords):
            logging.info(f"Ignoring {url} because it does not contain the required keywords")
            self.ignore_links.add(url)
            return

        # Handle links
        await self._handle_links(soup, url)

        if url not in self.urls_crawled and url not in self.ignore_links:
            self.urls_crawled.add(url)

        logging.info(f"Finished crawling {url}. Total: {len(self.urls_crawled)} links.")
        if not self.is_shutdown():
            await self.call_next(soup, url)

    async def _handle_links(self, soup, url):
        """
        Checks the links in the soup and adds them to the to_crawl_queue if they are not in the ignore list, not in the
        found list, and not in the to_crawl_set.
        Args:
            soup: BeautifulSoup object
            url: URL of the page

        Returns:

        """
        for a_tag in soup.find_all("a", href=True):
            found_link = a_tag.get("href")

            # Check if link is a fragment
            if found_link.startswith("#"):
                continue

            # Check if link is relative
            if found_link.startswith("/"):
                base_url = get_base_url(url)
                found_link = get_full_url(base_url, found_link)
            elif found_link.startswith("../"):
                base_url = get_base_url(url)
                found_link = get_full_url(base_url, found_link)

            # Check if link is an email
            if found_link.startswith("mailto:"):
                continue

            # Check if link is a phone number
            if found_link.startswith("tel:"):
                continue

            # Check if link is a file
            if found_link.endswith((".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".csv", ".zip", ".rar",
                                    ".tar", ".gz", ".7z", ".mp3", ".mp4", ".avi", ".mkv", ".mov", ".flv", ".wav",
                                    ".ogg", ".webm", ".m4a", ".flac", ".aac", ".wma", ".jpg", ".jpeg", ".png", ".gif",
                                    ".bmp", ".svg", ".webp")):
                continue

            if (found_link not in self.ignore_links
                    and found_link not in self.urls_crawled
                    and found_link not in self.to_crawl_set
                    and found_link.startswith("http")):
                self.to_crawl_queue.append(found_link)
                self.to_crawl_set.add(found_link)

    async def _fetch(self, session, url: str) -> str or None:
        """
        Fetches the content of a URL using the given session.
        Args:
            session:
            url:

        Returns: the HTML content of the URL
        """

        max_retries = self.max_retries
        retry_delay = self.retry_delay

        self._page_count += 1
        for attempt in range(max_retries):
            logging.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})" if attempt > 0 else f"Fetching {url}")
            try:
                async with session.get(url, timeout=self.timeout, headers=self.headers) as response:
                    response.raise_for_status()
                    html_text = await response.text()
                    return html_text
            except (TimeoutError, ClientError) as e:
                if attempt == max_retries - 1:
                    log_error(f"Failed to process {url} after {max_retries} attempts: {str(e)}")
                    return
                # Exponential wait time
                await asyncio.sleep(retry_delay * (2 ** attempt))
            except Exception as e:
                log_error(f"Error fetching {url}: {e}")
            return None

    def save_state(self):
        """
        Saves the global state to a file.
        """

        # Create directory for crawler states
        if not os.path.exists("crawler_states"):
            os.makedirs("crawler_states")

        with open(f"crawler_states/global.json", "w") as f:
            # Write it as json
            f.write(json.dumps({
                "to_crawl": list(self.to_crawl_queue),
                "ignore_links": list(self.ignore_links),
                "found_links": list(self.urls_crawled)
            }))

    def _load_state(self):
        """
        Loads the global state from a file into memory.
        """

        if not os.path.exists(f"crawler_states/global.json"):
            logging.info("No global state found")
            self.to_crawl_queue = collections.deque(SEEDS)
            return

        with open(f"crawler_states/global.json", "r") as f:
            data = json.loads(f.read())
            self.to_crawl_queue = collections.deque(data["to_crawl"])
            self.to_crawl_set = set(data["to_crawl"])
            self.ignore_links = set(data["ignore_links"])
            self.urls_crawled = set(data["found_links"])


# IMPORTANT: Please use main.py instead of this file
if __name__ == "__main__":
    con = duckdb.connect("crawlies.db")
    con.install_extension("fts")
    con.load_extension("fts")

    crawler = Crawler(con)
    crawler.process()
    con.close()
