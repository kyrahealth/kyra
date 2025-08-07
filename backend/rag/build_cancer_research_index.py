#!/usr/bin/env python3
"""
Cancer Research UK Sitemap Indexer
Extracts all URLs from the Cancer Research UK sitemap and embeds them into the vector store.
"""

import os
import pathlib
import re
import sys
import requests
import time
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from chromadb import PersistentClient
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.core import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from dotenv import load_dotenv
import openai

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
SITEMAP_URL = "https://www.cancerresearchuk.org/sitemap"
BASE_URL = "https://www.cancerresearchuk.org"
MAX_PAGES = 1000  # Limit to prevent overwhelming the system
REQUEST_DELAY = 1  # Delay between requests in seconds
TIMEOUT = 30

# Keywords to filter for cancer-related content
CANCER_KEYWORDS = [
    'cancer', 'tumour', 'tumor', 'oncology', 'carcinoma', 'sarcoma', 
    'leukemia', 'lymphoma', 'melanoma', 'screening', 'diagnosis',
    'treatment', 'symptoms', 'prevention', 'research', 'clinical',
    'therapy', 'chemotherapy', 'radiotherapy', 'surgery'
]

def is_cancer_related(url: str, title: str = "", content: str = "") -> bool:
    """Check if a URL or content is cancer-related."""
    url_lower = url.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Check URL for cancer-related keywords
    for keyword in CANCER_KEYWORDS:
        if keyword in url_lower:
            return True
    
    # Check title and content
    for keyword in CANCER_KEYWORDS:
        if keyword in title_lower or keyword in content_lower:
            return True
    
    return False

def extract_urls_from_sitemap(sitemap_url: str) -> Set[str]:
    """Extract all URLs from the Cancer Research UK sitemap."""
    print(f"🔍 Extracting URLs from sitemap: {sitemap_url}")
    
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
        
        print(f"📊 Found {len(urls)} URLs in sitemap")
        return urls
        
    except Exception as e:
        print(f"❌ Error extracting URLs from sitemap: {e}")
        return set()

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
    """Convert HTML to clean text."""
    try:
        soup = BeautifulSoup(p.read_text(encoding="utf-8"), "lxml")
        
        # Remove unwanted elements
        for element in soup(["nav", "footer", "aside", "script", "style", "header"]):
            element.decompose()
        
        # Get title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # Get main content
        text = soup.get_text(" ", strip=True)
        
        # Combine title and content
        if title:
            return f"Title: {title}\n\n{text}"
        return text
        
    except Exception as e:
        print(f"❌ Error processing {p}: {e}")
        return ""

def filter_relevant_urls(urls: Set[str]) -> List[str]:
    """Filter URLs to only include cancer-related content."""
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
                
                if is_cancer_related(url, title_text):
                    relevant_urls.append(url)
                    
        except Exception as e:
            print(f"⚠️  Error checking {url}: {e}")
            continue
    
    print(f"✅ Found {len(relevant_urls)} relevant URLs out of {total_urls}")
    return relevant_urls

def main():
    """Main function to build the Cancer Research UK index."""
    print("🚀 Starting Cancer Research UK sitemap indexing...")
    
    # Extract URLs from sitemap
    all_urls = extract_urls_from_sitemap(SITEMAP_URL)
    if not all_urls:
        print("❌ No URLs found in sitemap")
        return
    
    # Filter for relevant content
    relevant_urls = filter_relevant_urls(all_urls)
    if not relevant_urls:
        print("❌ No relevant URLs found")
        return
    
    # Fetch and process documents
    print(f"📥 Processing {len(relevant_urls)} documents...")
    docs = []
    
    for i, url in enumerate(relevant_urls, 1):
        print(f"📄 Processing {i}/{len(relevant_urls)}: {url}")
        
        html_file = fetch_with_retry(url)
        if html_file:
            text = html_to_text(html_file)
            if text.strip():
                doc = Document(
                    text=text,
                    metadata={
                        "source": url,
                        "title": url.split('/')[-1] if url.split('/')[-1] else url,
                        "domain": "cancerresearchuk.org"
                    }
                )
                docs.append(doc)
    
    print(f"✅ Successfully processed {len(docs)} documents")
    
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
    
    print(f"✅ Successfully embedded {final_count} documents")
    print(f"📁 Index saved to: {PERSIST_DIR}")
    print(f"📊 Total documents processed: {len(docs)}")

if __name__ == "__main__":
    main() 