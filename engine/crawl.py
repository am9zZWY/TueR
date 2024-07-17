# General
import asyncio
import collections  # For deque
import json
# Parsing
from bs4 import BeautifulSoup  # HTML parsing
from aiohttp import ClientSession, TCPConnector, ClientError, ClientTimeout
from utils import check_robots, get_base_url, get_full_url
# Threading
from pipeline import PipelineElement
# Language detection
from eld import LanguageDetector
# Database
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
SILENT_WARNINGS = False


def log_error(error_msg):
    """
    Prints an error message if SILENT_ERRORS is False.
    Args:
        error_msg: The error message to print.

    Returns:

    """
    if not SILENT_ERRORS:
        print(error_msg)


def log_warning(warning_msg):
    """
    Prints a warning message if SILENT_ERRORS is False.
    Args:
        warning_msg: The warning message to print.

    Returns:

    """
    if not SILENT_WARNINGS:
        print(warning_msg)


class Crawler(PipelineElement):
    def __init__(self, dbcon: duckdb.DuckDBPyConnection):
        super().__init__("Crawler")

        # Initialize the duckdb connection
        self.cursor = dbcon.cursor()

        # Page count
        self._page_count = 0

        # Crawler configuration
        self.timeout = 2  # Timeout in seconds
        self.max_retries = 3  # Maximum number of retries
        self.retry_delay = 1  # Delay between retries in seconds
        self.max_size = 1000  # Maximum number of pages to crawl
        self.max_concurrent = 10  # Maximum number of concurrent requests
        self.rate_limit = 10  # Rate limit in seconds
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
            "Safari/537.36 (Tuebingen University Web Crawling Project)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
            "Safari/537.36 (Tuebingen University Web Crawler)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
            "Safari/537.36 (Tuebingen University Research Crawler)",
        ]
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        # Crawler state
        self.currently_crawled = set()
        self.urls_crawled = set()
        self.ignore_links = set()
        self.to_crawl_queue = collections.deque(SEEDS)
        self.to_crawl_set = set(self.to_crawl_queue)
        # Load state
        self._load_state()

        # Crawling
        self._max_concurrent = self.max_concurrent
        self._timeout = ClientTimeout(total=10, connect=5, sock_read=5, sock_connect=5)
        self._connector = TCPConnector(
            limit=100,  # Limit concurrent connections
            force_close=True,
            enable_cleanup_closed=True,
            ssl=False,  # Disable SSL verification for speed (use with caution)
            ttl_dns_cache=300,  # Cache DNS results for 5 minutes
        )
        self._semaphore = asyncio.Semaphore(self._max_concurrent)

    def __del__(self) -> None:
        self.cursor.close()

    @property
    def user_agent(self):
        # Cycle through user agents
        return self.user_agents[self._page_count % len(self.user_agents)]

    async def process(self):
        """
        Starts the crawling process.
        Is called in the Pipeline.
        Returns: None

        """
        async with ClientSession(connector=self._connector, timeout=self._timeout) as session:
            tasks = set()
            while not self.is_shutdown() and len(self.urls_crawled) < self.max_size:
                while len(tasks) < self.max_concurrent and self.to_crawl_queue:
                    url = self.to_crawl_queue.popleft()
                    if url not in self.ignore_links and url not in self.urls_crawled:
                        task = asyncio.create_task(self._process_url_with_semaphore(session, url))
                        tasks.add(task)

                if not tasks:
                    break

                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                for task in done:
                    try:
                        await task
                    except Exception as e:
                        log_error(f"Unhandled exception in task: {e}")

                if self.is_shutdown():
                    break

            if self.is_shutdown():
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                self.save_state()

        print("Crawler finished processing")

    async def _process_url_with_semaphore(self, session, url: str):
        """
        Wrapper for _process_url that uses a semaphore to limit the number of concurrent requests.
        Args:
            session: aiohttp ClientSession
            url: URL to crawl

        Returns: None

        """
        async with self._semaphore:
            await self._process_url(session, url)

    async def _process_url(self, session, url: str):
        """
        Crawls a URL and processes the content.
        Args:
            session: aiohttp ClientSession
            url: URL to crawl

        Returns: None
        """
        if url in self.currently_crawled:
            log_warning(f"Ignoring {url} because it is already being crawled")
            return

        if len(self.urls_crawled) >= self.max_size:
            log_warning("Maximum size reached")
            return

        if not url.startswith("http"):
            log_warning(f"Invalid URL: {url}")
            return

        if any(domain in url for domain in self.ignore_domains):
            log_warning(f"Ignoring {url} because it is in the ignore domains list")
            self.ignore_links.add(url)
            return

        if url in self.ignore_links or url in self.urls_crawled:
            log_warning(f"Ignoring {url} because it is in the ignore or found list")
            return

        if not check_robots(url):
            log_warning(f"Ignoring {url} because it is disallowed by robots.txt")
            self.ignore_links.add(url)
            return

        self.currently_crawled.add(url)
        html_content = await self._fetch(session, url)
        if html_content is None:
            log_warning(f"Error fetching {url}")
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
            log_warning(f"Ignoring {url} because it is empty")
            self.ignore_links.add(url)
            return

        check_html_tag_lang = soup.find("html").get("lang") in self.langs
        check_xml_tag_lang = soup.find("html").get("xml:lang") in self.langs
        check_link_lang = any(split == lang for split in url.split("/") for lang in self.langs)
        check_text_lang = LANG_DETECTOR.detect(text) in self.langs

        if not check_html_tag_lang and not check_xml_tag_lang and not check_link_lang and not check_text_lang:
            log_warning(f"Ignoring {url} because it is not in the correct language")
            self.ignore_links.add(url)
            return

        if not any(keyword in text for keyword in self.required_keywords):
            log_warning(f"Ignoring {url} because it does not contain the required keywords")
            self.ignore_links.add(url)
            return

        # Handle links
        await self._handle_links(soup, url)

        if url not in self.urls_crawled and url not in self.ignore_links:
            self.urls_crawled.add(url)

        print(f"Finished crawling {url}. Total: {len(self.urls_crawled)} links.")
        # Remove from currently crawled
        self.currently_crawled.remove(url)
        if not self.is_shutdown():
            await self.call_next(soup, url)

    async def _handle_links(self, soup: BeautifulSoup, url: str):
        """
        Checks the links in the soup and adds them to the to_crawl_queue if they are not in the ignore list, not in the
        found list, and not in the to_crawl_set.
        Args:
            soup: BeautifulSoup object
            url: URL of the page

        Returns: None

        """
        for a_tag in soup.find_all("a", href=True):
            found_link = a_tag.get("href")

            # Check if link is a fragment
            if found_link.startswith("#"):
                continue

            # Strip out the fragment
            found_link = found_link.split("#")[0]

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
            session: aiohttp ClientSession
            url: URL to fetch

        Returns: the HTML content of the URL
        """

        max_retries = self.max_retries
        retry_delay = self.retry_delay

        self._page_count += 1
        for attempt in range(max_retries):
            print(f"Fetching {url} (attempt {attempt + 1}/{max_retries})" if attempt > 0 else f"Fetching {url}")
            try:
                async with session.get(url, timeout=self._timeout, headers=self.headers) as response:
                    response.raise_for_status()
                    return await response.text()
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
            print("No global state found")
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
