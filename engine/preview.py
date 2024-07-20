import urllib

from aiohttp import ClientSession
from bs4 import BeautifulSoup


async def load_preview(url: str) -> BeautifulSoup:
    """
    Load a preview of the page by requesting the URL and returning the full HTML content
    including CSS and JavaScript
    Args:
        url: The URL to fetch

    Returns:
        A Response containing the full HTML content with inlined CSS and JavaScript
    """

    print(f"Fetching preview for {url}")

    async with ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()

    soup = BeautifulSoup(html_content, 'html.parser')
    return soup
