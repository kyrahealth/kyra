from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import asyncio

router = APIRouter(prefix="/api/v1")

class LinkPreview(BaseModel):
    title: str
    description: str
    image: str | None = None
    favicon: str | None = None
    domain: str
    url: str

@router.get("/link-preview")
async def get_link_preview(url: str):
    """
    Fetch metadata for a given URL to create rich previews
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="Invalid URL")
        
        # Set up headers to appear as a regular browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Fetch the page with timeout
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract metadata
        preview = extract_metadata(soup, url)
        return preview
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Request timeout")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching preview: {str(e)}")

def extract_metadata(soup: BeautifulSoup, url: str) -> LinkPreview:
    """
    Extract metadata from HTML soup
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('www.', '')
    
    # Try to get title from various sources
    title = (
        get_meta_content(soup, 'og:title') or
        get_meta_content(soup, 'twitter:title') or
        (soup.find('title') and soup.find('title').get_text().strip()) or
        f"Content from {domain}"
    )
    
    # Try to get description
    description = (
        get_meta_content(soup, 'og:description') or
        get_meta_content(soup, 'twitter:description') or
        get_meta_content(soup, 'description') or
        extract_first_paragraph(soup) or
        f"Visit {domain} for more information"
    )
    
    # Try to get image
    image = (
        get_meta_content(soup, 'og:image') or
        get_meta_content(soup, 'twitter:image') or
        find_first_image(soup, url)
    )
    
    # Try to get favicon
    favicon = find_favicon(soup, url)
    
    # Clean up title and description
    title = clean_text(title)[:100]
    description = clean_text(description)[:200]
    
    return LinkPreview(
        title=title,
        description=description,
        image=make_absolute_url(image, url) if image else None,
        favicon=make_absolute_url(favicon, url) if favicon else None,
        domain=domain,
        url=url
    )

def get_meta_content(soup: BeautifulSoup, property_name: str) -> str | None:
    """Get content from meta tag"""
    # Try property attribute (Open Graph)
    meta = soup.find('meta', property=property_name)
    if meta and meta.get('content'):
        return meta.get('content')
    
    # Try name attribute (Twitter, description)
    meta = soup.find('meta', attrs={'name': property_name})
    if meta and meta.get('content'):
        return meta.get('content')
    
    return None

def extract_first_paragraph(soup: BeautifulSoup) -> str | None:
    """Extract first meaningful paragraph"""
    # Find the first paragraph with substantial text
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        if len(text) > 50:  # Only paragraphs with meaningful content
            return text
    return None

def find_first_image(soup: BeautifulSoup, base_url: str) -> str | None:
    """Find the first meaningful image"""
    # Look for images that are likely to be content images
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'badge']):
            # Check if image has reasonable dimensions
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    w, h = int(width), int(height)
                    if w >= 200 and h >= 200:  # Reasonable size
                        return src
                except ValueError:
                    continue
            else:
                return src  # No dimensions specified, assume it's fine
    return None

def find_favicon(soup: BeautifulSoup, base_url: str) -> str | None:
    """Find favicon"""
    # Try various favicon selectors
    selectors = [
        'link[rel="icon"]',
        'link[rel="shortcut icon"]',
        'link[rel="apple-touch-icon"]',
    ]
    
    for selector in selectors:
        favicon = soup.select_one(selector)
        if favicon and favicon.get('href'):
            return favicon.get('href')
    
    # Default favicon location
    parsed_url = urlparse(base_url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"

def make_absolute_url(url: str | None, base_url: str) -> str | None:
    """Convert relative URL to absolute"""
    if not url:
        return None
    return urljoin(base_url, url)

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common prefixes/suffixes
    text = re.sub(r'^(Home\s*[-|]\s*)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*[-|]\s*[^-|]*$', '', text)  # Remove site name suffix
    
    return text