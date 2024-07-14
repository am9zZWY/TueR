import urllib
from urllib.parse import urlparse, urljoin  # Parsing URLs
# Robots.txt
import urllib.robotparser  # For checking robots.txt


def get_domain(url: str) -> str:
    """
    Extracts the domain from a URL.

    Parameters:
    - `url` (str): The URL to extract the domain from.

    Returns:
    - `str`: The domain of the URL.
    """

    return urlparse(url).netloc


def get_full_url(base_url, relative_url):
    """
    Converts a relative URL to a full URL based on the base URL.

    Parameters:
    - `base_url` (str): The base URL.
    - `relative_url` (str): The relative URL to convert.

    Returns:
    - `str`: The full URL.
    """
    return urljoin(base_url, relative_url)


def get_base_url(url: str) -> str:
    """
    Extracts the base URL from a URL.

    Parameters:
    - `url` (str): The URL to extract the base URL from.

    Returns:
    - `str`: The base URL of the URL.
    """
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


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
