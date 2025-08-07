#!/usr/bin/env python3
"""
Advanced Cancer Research UK Indexer
Handles multiple sitemap formats and provides sophisticated filtering options.
"""

import os
import pathlib
import re
import sys
import requests
import time
import xml.etree.ElementTree as ET
from typing import List, Set, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from chromadb import PersistentClient
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.core import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from dotenv import load_dotenv
import openai
import json

load_dotenv(override=True)

# -------- paths --------
ROOT = pathlib.Path(__file__).parent
PERSIST_DIR = ROOT / "chroma_db"
RAW_HTML_DIR = ROOT / "html"
RAW_HTML_DIR.mkdir(exist_ok=True)

# -------- sanity checks --------
key = os.getenv("OPENAI_API_KEY")
if not key:
    sys.exit("❌  OPENAI_API_KEY is NOT set – export it or put it in .env first.")
openai.api_key = key
print("✅  Using OPENAI_API_KEY =", key[:10], "...")

# -------- configuration --------
SITEMAP_URLS = [
    "https://www.cancerresearchuk.org/sitemap",
    "https://www.cancerresearchuk.org/sitemap.xml",  # Try XML sitemap if available
]
BASE_URL = "https://www.cancerresearchuk.org"
MAX_PAGES = 2000  # Increased limit for comprehensive coverage
REQUEST_DELAY = 0.5  # Reduced delay for faster processing
TIMEOUT = 30

# Cancer-related keywords for filtering
CANCER_KEYWORDS = [
    'cancer', 'tumour', 'tumor', 'oncology', 'carcinoma', 'sarcoma', 
    'leukemia', 'lymphoma', 'melanoma', 'screening', 'diagnosis',
    'treatment', 'symptoms', 'prevention', 'research', 'clinical',
    'therapy', 'chemotherapy', 'radiotherapy', 'surgery', 'biopsy',
    'metastasis', 'remission', 'prognosis', 'staging', 'grade',
    'mammogram', 'colonoscopy', 'endoscopy', 'biomarker', 'immunotherapy'
]

# Categories to focus on
CANCER_CATEGORIES = [
    'about-cancer', 'cancer-types', 'causes', 'symptoms', 'diagnosis',
    'treatment', 'living-with-cancer', 'research', 'clinical-trials',
    'prevention', 'screening', 'statistics', 'information'
]

def is_cancer_related(url: str, title: str = "", content: str = "") -> bool:
    """Enhanced check for cancer-related content."""
    url_lower = url.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Check for cancer categories in URL
    for category in CANCER_CATEGORIES:
        if category in url_lower:
            return True
    
    # Check for cancer keywords
    for keyword in CANCER_KEYWORDS:
        if keyword in url_lower or keyword in title_lower or keyword in content_lower:
            return True
    
    return False

def extract_urls_from_html_sitemap(sitemap_url: str) -> Set[str]:
    """Extract URLs from HTML sitemap."""
    print(f"🔍 Extracting URLs from HTML sitemap: {sitemap_url}")
    
    try:
        response = requests.get(sitemap_url, timeout=TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        urls = set()
        
        # Find all links in the sitemap
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = urljoin(BASE_URL, href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                # Only include Cancer Research UK URLs
                if 'cancerresearchuk.org' in full_url:
                    urls.add(full_url)
        
        print(f"📊 Found {len(urls)} URLs in HTML sitemap")
        return urls
        
    except Exception as e:
        print(f"❌ Error extracting URLs from HTML sitemap: {e}")
        return set()

def extract_urls_from_xml_sitemap(sitemap_url: str) -> Set[str]:
    """Extract URLs from XML sitemap."""
    print(f"🔍 Extracting URLs from XML sitemap: {sitemap_url}")
    
    try:
        response = requests.get(sitemap_url, timeout=TIMEOUT)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Handle different XML sitemap formats
        urls = set()
        
        # Try standard sitemap format
        for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc_elem is not None:
                url = loc_elem.text
                if url and 'cancerresearchuk.org' in url:
                    urls.add(url)
        
        # If no URLs found, try alternative format
        if not urls:
            for url_elem in root.findall('.//url'):
                loc_elem = url_elem.find('loc')
                if loc_elem is not None:
                    url = loc_elem.text
                    if url and 'cancerresearchuk.org' in url:
                        urls.add(url)
        
        print(f"📊 Found {len(urls)} URLs in XML sitemap")
        return urls
        
    except Exception as e:
        print(f"❌ Error extracting URLs from XML sitemap: {e}")
        return set()

def extract_all_urls() -> Set[str]:
    """Extract URLs from all available sitemaps."""
    all_urls = set()
    
    for sitemap_url in SITEMAP_URLS:
        if sitemap_url.endswith('.xml'):
            urls = extract_urls_from_xml_sitemap(sitemap_url)
        else:
            urls = extract_urls_from_html_sitemap(sitemap_url)
        
        all_urls.update(urls)
    
    print(f"📊 Total unique URLs found: {len(all_urls)}")
    return all_urls

def fetch_with_retry(url: str, max_retries: int = 3) -> Optional[pathlib.Path]:
    """Fetch a URL with retry logic and save to file."""
    fname = RAW_HTML_DIR / (re.sub(r"[^a-z0-9]+", "_", url.lower().split("//")[1]) + ".html")
    
    if fname.exists():
        print(f"📁 Using cached: {url}")
        return fname
    
    for attempt in range(max_retries):
        try:
            print(f"⇢ Downloading ({attempt + 1}/{max_retries}): {url}")
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            
            # Save the HTML content
            fname.write_text(response.text, encoding="utf-8")
            
            # Add delay to be respectful to the server
            time.sleep(REQUEST_DELAY)
            
            return fname
            
        except Exception as e:
            print(f"⚠️  Attempt {attempt + 1} failed for {url}: {e}")
            if attempt == max_retries - 1:
                print(f"❌ Failed to fetch {url} after {max_retries} attempts")
                return None
            time.sleep(REQUEST_DELAY * (attempt + 1))  # Exponential backoff
    
    return None

def html_to_text(p: pathlib.Path) -> str:
    """Convert HTML to clean text with enhanced processing."""
    try:
        soup = BeautifulSoup(p.read_text(encoding="utf-8"), "lxml")
        
        # Remove unwanted elements
        for element in soup(["nav", "footer", "aside", "script", "style", "header", "form"]):
            element.decompose()
        
        # Get title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # Get main content - focus on main content areas
        main_content = ""
        
        # Try to find main content areas
        main_selectors = ['main', '[role="main"]', '.main-content', '#main-content', '.content']
        for selector in main_selectors:
            main_elem = soup.select_one(selector)
            if main_elem:
                main_content = main_elem.get_text(" ", strip=True)
                break
        
        # If no main content found, use body
        if not main_content:
            body = soup.find('body')
            if body:
                main_content = body.get_text(" ", strip=True)
        
        # Clean up text
        text = re.sub(r'\s+', ' ', main_content).strip()
        
        # Combine title and content
        if title:
            return f"Title: {title}\n\n{text}"
        return text
        
    except Exception as e:
        print(f"❌ Error processing {p}: {e}")
        return ""

def filter_relevant_urls(urls: Set[str]) -> List[str]:
    """Filter URLs to only include cancer-related content with enhanced logic."""
    print("🔍 Filtering URLs for cancer-related content...")
    
    relevant_urls = []
    total_urls = len(urls)
    
    for i, url in enumerate(urls, 1):
        if i > MAX_PAGES:
            print(f"⚠️  Reached maximum page limit ({MAX_PAGES})")
            break
            
        print(f"🔍 Checking {i}/{total_urls}: {url}")
        
        # Quick check based on URL
        if is_cancer_related(url):
            relevant_urls.append(url)
            continue
        
        # If URL doesn't contain cancer keywords, fetch and check content
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                title_text = title.get_text(strip=True) if title else ""
                
                # Get a sample of content for keyword checking
                body = soup.find('body')
                content_sample = body.get_text()[:1000] if body else ""
                
                if is_cancer_related(url, title_text, content_sample):
                    relevant_urls.append(url)
                    
        except Exception as e:
            print(f"⚠️  Error checking {url}: {e}")
            continue
    
    print(f"✅ Found {len(relevant_urls)} relevant URLs out of {total_urls}")
    return relevant_urls

def save_processing_stats(stats: Dict[str, Any]):
    """Save processing statistics to a JSON file."""
    stats_file = ROOT / "processing_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"📊 Statistics saved to: {stats_file}")

def main():
    """Main function to build the Cancer Research UK index."""
    print("🚀 Starting Advanced Cancer Research UK sitemap indexing...")
    
    # Extract URLs from all sitemaps
    all_urls = extract_all_urls()
    if not all_urls:
        print("❌ No URLs found in sitemaps")
        return
    
    # Filter for relevant content
    relevant_urls = filter_relevant_urls(all_urls)
    if not relevant_urls:
        print("❌ No relevant URLs found")
        return
    
    # Fetch and process documents
    print(f"📥 Processing {len(relevant_urls)} documents...")
    docs = []
    failed_urls = []
    
    for i, url in enumerate(relevant_urls, 1):
        print(f"📄 Processing {i}/{len(relevant_urls)}: {url}")
        
        html_file = fetch_with_retry(url)
        if html_file:
            text = html_to_text(html_file)
            if text.strip():
                # Extract title from URL or content
                title = url.split('/')[-1] if url.split('/')[-1] else url
                
                doc = Document(
                    text=text,
                    metadata={
                        "source": url,
                        "title": title,
                        "domain": "cancerresearchuk.org",
                        "category": "cancer_research"
                    }
                )
                docs.append(doc)
            else:
                failed_urls.append(url)
        else:
            failed_urls.append(url)
    
    print(f"✅ Successfully processed {len(docs)} documents")
    print(f"❌ Failed to process {len(failed_urls)} URLs")
    
    if not docs:
        print("❌ No documents to embed")
        return
    
    # Set up embedding model
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    
    # Set up vector store
    client = PersistentClient(path=str(PERSIST_DIR))
    collection = client.get_or_create_collection("cancer_research_docs")
    store = ChromaVectorStore(chroma_collection=collection, stores_text=True)
    
    # Create storage context
    storage_ctx = StorageContext.from_defaults(vector_store=store)
    
    print("⇢ Embedding documents...")
    index = VectorStoreIndex.from_documents(
        docs,
        storage_context=storage_ctx,
        show_progress=True,
    )
    
    # Persist the index
    print("💾 Persisting index...")
    index.storage_context.persist(persist_dir=str(PERSIST_DIR))
    
    # Verify the results
    final_count = PersistentClient(path=str(PERSIST_DIR))\
                    .get_or_create_collection("cancer_research_docs").count()
    
    # Save processing statistics
    stats = {
        "total_urls_found": len(all_urls),
        "relevant_urls_found": len(relevant_urls),
        "successfully_processed": len(docs),
        "failed_urls": failed_urls,
        "final_embedded_count": final_count,
        "timestamp": time.time()
    }
    save_processing_stats(stats)
    
    print(f"✅ Successfully embedded {final_count} documents")
    print(f"📁 Index saved to: {PERSIST_DIR}")
    print(f"📊 Total documents processed: {len(docs)}")
    print(f"📈 Success rate: {len(docs)/len(relevant_urls)*100:.1f}%")

if __name__ == "__main__":
    main() 