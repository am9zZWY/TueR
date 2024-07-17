import asyncio
import lzma
import pickle

import aiofiles
import hashlib
import os

from bs4 import BeautifulSoup

from pipeline import PipelineElement


def generate_filename(url):
    """
    Generates a unique filename based on the URL.
    """
    # Use MD5 hash of the URL as the filename
    return hashlib.md5(url.encode()).hexdigest() + '.tuer'


class Downloader(PipelineElement):
    def __init__(self, storage_dir='downloads'):
        super().__init__("Downloader")
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    async def process(self, data, link):
        """
        Writes the BeautifulSoup object to a file if it's not None.
        """
        if data is None or not isinstance(data, BeautifulSoup):
            print(f"Failed to process {link}. Invalid or empty data.")
            return

        # Generate a unique filename based on the URL
        filename = generate_filename(link)
        filepath = os.path.join(self.storage_dir, filename)

        # Serialize and write the BeautifulSoup object to a file
        try:
            async with aiofiles.open(filepath, 'wb') as f:
                dump = {
                    'url': link,
                    'data': lzma.compress(pickle.dumps(data))
                }
                await f.write(pickle.dumps(dump))
            print(f"Successfully saved {link} to {filepath}")
        except Exception as e:
            print(f"Error saving {link}: {str(e)}")


async def decompress_html(filepath: str) -> tuple[BeautifulSoup, str]:
    """
    Decompresses and deserializes the BeautifulSoup object from a file.
    """
    try:
        async with aiofiles.open(filepath, 'rb') as f:
            data = await f.read()
        load = pickle.loads(data)
        soup = pickle.loads(lzma.decompress(load['data']))
        link = load['url']
        print(f"Successfully loaded {link} from {filepath}")
        return soup, link
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")


class Loader(PipelineElement):
    def __init__(self, storage_dir='downloads'):
        super().__init__("Loader")
        self.storage_dir = storage_dir
        self.lock = asyncio.Lock()
        self._file_list = self._get_file_list()

    async def process(self):
        """
        Loads the BeautifulSoup object from a file, one at a time.
        """

        while self._file_list:
            await self.lock.acquire()
            try:
                filename = self._file_list.pop(0)
            except IndexError:
                self.lock.release()
                continue
            finally:
                self.lock.release()
            filepath = os.path.join(self.storage_dir, filename)

            if not os.path.exists(filepath):
                print(f"File not found: {filepath}")
                continue

            # Decompress and deserialize the BeautifulSoup object
            soup, link = await decompress_html(filepath)
            if soup is not None:
                await self.call_next(soup, link)

    def _get_file_list(self) -> list[str]:
        """
        Returns a list of files in the specified directory.
        """
        if not os.path.exists(self.storage_dir):
            return []

        return [f for f in os.listdir(self.storage_dir) if os.path.isfile(os.path.join(self.storage_dir, f))]
