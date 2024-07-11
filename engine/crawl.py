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
from custom_db import *

##### Constants #####
# Maximum size of the links
MAX_SIZE = 20
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
    def __init__(self):
        super().__init__("Crawler")

        # Initialize the crawler state
        self.found_links = set()
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
        self.user_agent = "Modern Search Engines University of Tuebingen Project Crawler (https://uni-tuebingen.de/de/262377)"

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

    async def process(self):
        print("Crawler started")
        async with ClientSession() as session:
            while self.to_crawl and len(self.found_links) < self.max_size:
                tasks = []
                for _ in range(min(MAX_SIZE, len(self.to_crawl))):
                    link = self.to_crawl.popleft()
                    self.to_crawl_set.remove(link)
                    tasks.append(self._handle_link(session, link))
                await asyncio.gather(*tasks)

    async def _handle_link(self, session, link):
        crawling_str = f"Crawler crawling {link}: "

        if not link.startswith("http"):
            print(crawling_str + "skipped")
            return

        if any(domain in link for domain in self.ignore_domains):
            print(crawling_str + "domain in ignore list")
            self.ignore_links.add(link)
            return

        if link in self.ignore_links or link in self.found_links:
            print(crawling_str + "already ignored or visited")
            return

        if not check_robots(link):
            print(crawling_str + "robots.txt disallows")
            self.ignore_links.add(link)
            return

        html_content = await self.fetch(session, link)
        if html_content is None:
            self.ignore_links.add(link)
            return

        soup = BeautifulSoup(html_content, "lxml")
        text = soup.get_text().lower()

        check_html_tag_lang = soup.find("html").get("lang") in self.langs
        check_xml_tag_lang = soup.find("html").get("xml:lang") in self.langs
        check_link_lang = any(split == lang for split in link.split("/") for lang in self.langs)
        check_text_lang = LANG_DETECTOR.detect(text) in self.langs

        if not check_html_tag_lang and not check_xml_tag_lang and not check_link_lang and not check_text_lang:
            print(crawling_str + "unsupported language")
            self.ignore_links.add(link)
            return

        if not any(keyword in text for keyword in self.required_keywords):
            self.ignore_links.add(link)
            print(crawling_str + "no required keywords")
            return

        for a_tag in soup.find_all("a", href=True):
            found_link = a_tag.get("href")
            if found_link.startswith("#"):
                continue

            if found_link.startswith("/"):
                base_url = get_base_url(link)
                found_link = base_url + found_link

            if found_link not in self.ignore_links and found_link not in self.found_links and found_link not in self.to_crawl_set and found_link.startswith(
                    "http"):
                self.to_crawl.append(found_link)
                self.to_crawl_set.add(found_link)

        if link not in self.found_links and link not in self.ignore_links:
            self.found_links.add(link)

        print(crawling_str + "done")
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
                "found_links": list(self.found_links)
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
            self.found_links = set(data["found_links"])


# IMPORTANT: Please use main.py instead of this file
if __name__ == "__main__":
    crawler = Crawler()
    crawler.process()
    # TODO - seperarw crawling and tokenizing
    index_pages()
    index_df = access_index()
    index_df.to_csv("inverted_index.csv")
    save_pages()
