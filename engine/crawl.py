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
LANG_DETECTOR = LanguageDetector()


class Crawler(PipelineElement):
    def __init__(self, dbcon: duckdb.DuckDBPyConnection):
        super().__init__("Crawler")

        # Initialize the duckdb connection
        self.cursor = dbcon.cursor()

        # Initialize the crawler state
        self.urls_crawled = set()
        self.ignore_links = set()
        self.to_crawl = collections.deque(SEEDS)
        self.to_crawl_set = set(self.to_crawl)

        # Load the global state
        self._load_state()

        self.max_size = 1000  # Example maximum size
        self.ignore_domains = ["github.com", "linkedin.com", "xing.com", "instagram.com", "twitter.com", "youtube.com",
                               "de.wikipedia.org", "wikipedia.org", "google.com", "google.de", "google.co.uk",
                               "amazon.com", "cctue.de", "spotify.com"]
        self.langs = ["en", "en-de", "eng", "en-GB", "en-US", "english"]
        self.required_keywords = ["tübingen", "tuebingen", "tubingen", "t%C3%BCbingen"]
        self.user_agent = ("Modern Search Engines University of Tuebingen Project Crawler ("
                           "https://uni-tuebingen.de/de/262377)")

    def __del__(self) -> None:
        self.cursor.close()

    async def fetch(self, session, url):
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        try:
            async with session.get(url, timeout=5, headers=headers) as response:
                return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    @staticmethod
    async def _fetch_with_playwright(url, max_retries=3):
        for attempt in range(max_retries):
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch()
                    page = await browser.new_page()
                    await page.goto(url, wait_until='networkidle')
                    content = await page.content()
                    await browser.close()
                    return content
            except Exception as e:
                print(f"Error on attempt {attempt + 1} for {url}: {e}")
                if attempt == max_retries - 1:
                    print(f"Max retries reached for {url}")
                    return None

    @staticmethod
    def _needs_javascript_rendering(html: str) -> bool:
        # Check for JavaScript frameworks
        if any(framework in html.lower() for framework in ['react', 'vue', 'angular']):
            return True

        return False

    async def process(self):
        async with ClientSession(connector=self._connector) as session:
            while not self.is_shutdown() and self.to_crawl and len(self.urls_crawled) < self.max_size:
                # Process multiple links concurrently
                tasks = []
                for _ in range(min(10, len(self.to_crawl))):  # Process up to 10 links at a time
                    if self.to_crawl and len(self.urls_crawled) < self.max_size:
                        link = self.to_crawl.popleft()
                        task = asyncio.create_task(self._handle_link(session, link))
                        tasks.append(task)
                    else:
                        break

                if not tasks:
                    break

                # Wait for all tasks to complete or for shutdown
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                # Process completed tasks
                for task in done:
                    try:
                        await task
                    except Exception as e:
                        print(f"Error processing link: {e}")

                # Check for shutdown
                if self.is_shutdown():
                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()
                    # Wait for cancellation to complete
                    await asyncio.gather(*pending, return_exceptions=True)
                    self.save_state()
                    break

        # Process any remaining items in the queue
        self.call_next()

    async def _handle_link(self, session, link):
        if len(self.urls_crawled) >= self.max_size:
            print("Maximum size reached")
            return

        print(f"Crawler crawling {link}...")

        if not link.startswith("http"):
            print(f"Invalid URL: {link}")
            return

        if any(domain in link for domain in self.ignore_domains):
            print(f"Ignoring {link} because it is in the ignore domains list")
            self.ignore_links.add(link)
            return

        if link in self.ignore_links or link in self.urls_crawled:
            print(f"Ignoring {link} because it is in the ignore or found list")
            return

        if not check_robots(link):
            print(f"Ignoring {link} because it is disallowed by robots.txt")
            self.ignore_links.add(link)
            return

        html_content = await self.fetch(session, link)
        if html_content is None:
            print(f"Error fetching {link}")
            self.ignore_links.add(link)
            return

        soup = BeautifulSoup(html_content, "lxml")
        text = soup.get_text().lower()

        check_html_tag_lang = soup.find("html").get("lang") in self.langs
        check_xml_tag_lang = soup.find("html").get("xml:lang") in self.langs
        check_link_lang = any(split == lang for split in link.split("/") for lang in self.langs)
        check_text_lang = LANG_DETECTOR.detect(text) in self.langs

        if not check_html_tag_lang and not check_xml_tag_lang and not check_link_lang and not check_text_lang:
            print(f"Ignoring {link} because it is not in the correct language")
            self.ignore_links.add(link)
            return

        if not any(keyword in text for keyword in self.required_keywords):
            print(f"Ignoring {link} because it does not contain the required keywords")
            self.ignore_links.add(link)
            return

        for a_tag in soup.find_all("a", href=True):
            found_link = a_tag.get("href")

            # Check if link is a fragment
            if found_link.startswith("#"):
                continue

            # Check if link is relative
            if found_link.startswith("/"):
                base_url = get_base_url(link)
                found_link = get_full_url(base_url, found_link)
            elif found_link.startswith("../"):
                base_url = get_base_url(link)
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
                self.to_crawl.append(found_link)
                self.to_crawl_set.add(found_link)

        if link not in self.urls_crawled and link not in self.ignore_links:
            self.urls_crawled.add(link)

        print(f"Finished crawling {link}. Total: {len(self.urls_crawled)} links.")
        self.call_next(soup, link)

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
                "to_crawl": list(self.to_crawl),
                "ignore_links": list(self.ignore_links),
                "found_links": list(self.urls_crawled)
            }))

    def _load_state(self):
        """
        Loads the global state from a file into memory.
        """

        if not os.path.exists(f"crawler_states/global.json"):
            print("No global state found")
            self.to_crawl = collections.deque(SEEDS)
            return

        with open(f"crawler_states/global.json", "r") as f:
            data = json.loads(f.read())
            self.to_crawl = collections.deque(data["to_crawl"])
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
