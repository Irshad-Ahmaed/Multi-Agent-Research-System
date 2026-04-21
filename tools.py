from langchain.tools import tool
import requests  # for making API calls to talk to internet
from bs4 import BeautifulSoup  # for parsing HTML content
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import logging

from tavily import TavilyClient  # for interacting with Tavily API
import os  # for accessing environment variables
from dotenv import load_dotenv  # for loading environment variables from .env file
from rich import print  # for pretty printing results
from tenacity import retry, stop_after_attempt, wait_exponential  # for retry logic

load_dotenv()  # load environment variables from .env file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# initialize Tavily client with API key from environment variable
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Retry decorator for network operations
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _make_request(url: str, timeout: int = 8) -> requests.Response:
    """Make an HTTP request with retry logic."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    resp = requests.get(url, timeout=timeout, headers=headers)
    resp.raise_for_status()
    return resp


@tool
def search_web(query: str) -> str:
    """Search the web for recent, relevant, and authentic information on the given query(topic). Returns title,urls, and snippets."""
    results = tavily.search(
        query, max_results=5)  # use Tavily's search method to get search results for the query

    out = []

    for r in results['results']:
        # out.append({
        #     "title": r['title'],
        #     "url": r['url'],
        #     "snippet": r['content'],
        #     "score": r['score']
        # })
    # return "\n-----\n".join(str(item) for item in out)

        # alternate method is formating the results as a string instead of a list of dictionaries, but this is less structured and harder to work with in code
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content']}\nScore: {r['score']}"
        )
    return "\n-----\n".join(out)



def _is_valid_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception:
        return False


def _extract_main_content(soup: BeautifulSoup) -> str:
    """
    Extract main content from parsed HTML using common content selectors.
    Looks for article, main, or largest text block.
    """
    # Try to find main content areas
    main_selectors = [
        'main',
        'article',
        {'class': ['content', 'main-content', 'post-content', 'entry-content']},
        {'id': ['content', 'main', 'article']},
    ]
    
    main_content = None
    for selector in main_selectors:
        if isinstance(selector, str):
            main_content = soup.find(selector)
        else:
            main_content = soup.find(**selector)
        if main_content:
            break
    
    # If no main content found, use body
    if not main_content:
        main_content = soup.find('body') or soup
    
    # Remove unwanted tags
    for tag in main_content(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        tag.decompose()
    
    # Extract text with proper spacing
    text = main_content.get_text(separator="\n", strip=True)
    # Clean up excessive whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)[:3000]


@tool
def scrape_url(url: str) -> str:
    """Scrape the content of a single URL and return it with the source URL."""
    
    if not _is_valid_url(url):
        return f"Error: Invalid URL format - {url}"
    
    try:
        resp = _make_request(url, timeout=8)
        
        # Validate content type
        content_type = resp.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            logger.warning(f"URL {url} returned non-HTML content: {content_type}")
            return f"Source: {url}\nWarning: Page is not HTML content ({content_type})"
        
        soup = BeautifulSoup(resp.text, "html.parser")
        text = _extract_main_content(soup)
        
        if not text or len(text.strip()) < 50:
            return f"Source: {url}\nWarning: Extracted very little content from {url}"
        
        # IMPORTANT: Include the source URL in the returned content
        return f"Source URL: {url}\n{'='*80}\n{text}"
        
    except requests.exceptions.Timeout:
        return f"Source: {url}\nError: Request timed out while scraping {url}"
    except requests.exceptions.HTTPError as e:
        return f"Source: {url}\nError: HTTP {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Source: {url}\nError: Network error - {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {str(e)}")
        return f"Source: {url}\nError scraping URL: {str(e)}"


@tool
def scrape_multiple_urls(urls: list[str]) -> dict:
    """
    Scrape multiple URLs in parallel using ThreadPoolExecutor.
    Returns a dict with results for each URL.
    
    Args:
        urls: List of URLs to scrape
        
    Returns:
        Dictionary mapping URLs to their scraped content
    """
    results = {}
    
    # Validate and filter URLs
    valid_urls = [url for url in urls if _is_valid_url(url)]
    if len(valid_urls) < len(urls):
        logger.warning(f"Filtered out {len(urls) - len(valid_urls)} invalid URLs")
    
    if not valid_urls:
        return {"error": "No valid URLs provided"}
    
    # Scrape in parallel (max 5 concurrent to be respectful to servers)
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(_scrape_single, url): url for url in valid_urls}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {str(e)}")
                results[url] = f"Error: {str(e)}"
    
    return results


def _scrape_single(url: str) -> str:
    """Helper function for parallel scraping (without @tool decorator)."""
    try:
        resp = _make_request(url, timeout=10)
        content_type = resp.headers.get('content-type', '').lower()
        
        if 'text/html' not in content_type:
            return f"Warning: Non-HTML content ({content_type})"
        
        soup = BeautifulSoup(resp.text, "html.parser")
        return _extract_main_content(soup)
        
    except requests.exceptions.Timeout:
        return f"Timeout error"
    except requests.exceptions.HTTPError as e:
        return f"HTTP {e.response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


# Async version for advanced use cases
async def _scrape_single_async(url: str, session: aiohttp.ClientSession) -> tuple[str, str]:
    """Asynchronously scrape a single URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), headers=headers) as resp:
            if resp.status != 200:
                return url, f"HTTP {resp.status}"
            
            text = await resp.text()
            soup = BeautifulSoup(text, "html.parser")
            content = _extract_main_content(soup)
            return url, content
            
    except asyncio.TimeoutError:
        return url, "Timeout error"
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return url, f"Error: {str(e)}"


@tool
def scrape_multiple_urls_async(urls: list[str]) -> dict:
    """
    Scrape multiple URLs in parallel using async/await for maximum efficiency.
    Best for 10+ URLs. Respects rate limiting.
    
    Args:
        urls: List of URLs to scrape
        
    Returns:
        Dictionary mapping URLs to their scraped content
    """
    valid_urls = [url for url in urls if _is_valid_url(url)]
    if not valid_urls:
        return {"error": "No valid URLs provided"}
    
    async def fetch_all():
        connector = aiohttp.TCPConnector(limit_per_host=2)  # Rate limiting: 2 concurrent per host
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [_scrape_single_async(url, session) for url in valid_urls]
            results = await asyncio.gather(*tasks)
            return dict(results)
    
    # Run async function
    try:
        results = asyncio.run(fetch_all())
        return results
    except Exception as e:
        logger.error(f"Error in async scraping: {str(e)}")
        return {"error": str(e)}
