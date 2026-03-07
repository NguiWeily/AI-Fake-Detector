import requests
from dotenv import load_dotenv
import os
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin

load_dotenv()
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8080")

def searxng_search(
    query: str,
    categories: Optional[List[str]] = None,
    engines: Optional[List[str]] = None,
    language: Optional[str] = None,
    pageno: int = 1,
    time_range: Optional[str] = None,
    format: str = "json",
    safesearch: int = 1,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Send a search query to a SearXNG search engine.
    Quick local set up for SearXNG via Docker can be found at
    https://docs.searxng.org/admin/installation-docker.html
    
    Args:
        query: The search query string
        categories: List of search categories (e.g., ["general", "images"])
        engines: List of specific engines to use (e.g., ["google", "bing"])
        language: Language code (e.g., "en", "de")
        pageno: Page number for pagination (default: 1)
        time_range: Time range filter ("day", "month", "year")
        format: Output format ("json", "csv", "rss")
        safesearch: Safe search level (0=off, 1=moderate, 2=strict)
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary containing search results
    
    Raises:
        requests.RequestException: If the request fails
        ValueError: If the response is not valid JSON (when format="json")
    """
    
    # Prepare the search endpoint URL
    search_url = urljoin(SEARXNG_URL, '/search')
    
    # Build parameters
    params = {
        'q': query,
        'pageno': pageno,
        'format': format,
        'safesearch': safesearch
    }
    
    # Add optional parameters
    if categories:
        params['categories'] = ','.join(categories)
    
    if engines:
        params['engines'] = ','.join(engines)
    
    if language:
        params['language'] = language
    
    if time_range:
        params['time_range'] = time_range
    
    # Make the request
    try:
        response = requests.get(search_url, params=params, timeout=timeout)
        response.raise_for_status()
        
        if format == 'json':
            return response.json()
        else:
            return {'raw_response': response.text, 'status_code': response.status_code}
            
    except requests.RequestException as e:
        raise requests.RequestException(f"SearXNG search failed: {str(e)}")
    except ValueError as e:
        if format == 'json':
            raise ValueError(f"Invalid JSON response from SearXNG: {str(e)}")
        raise