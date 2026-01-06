import requests
from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)

def scrape_url(url: str, max_length: int = 5000) -> str:
    """
    Fetches the content of a URL and returns the visible text.
    
    Args:
        url (str): The URL to scrape.
        max_length (int): Maximum number of characters to return.
        
    Returns:
        str: Cleaned text content from the webpage, or None if failed.
    """
    try:
        # User agent to avoid some basic bot blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, and navigation elements that corrupt text context
        for element in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
            element.extract()
            
        # Get text
        text = soup.get_text(separator=' ')
        
        # Clean up whitespace
        # 1. Replace multiple spaces/tabs with single space
        text = re.sub(r'\s+', ' ', text)
        # 2. Trim
        text = text.strip()
        
        if not text:
            return None
            
        return text[:max_length]
        
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return None
