# debug_build_index.py   – run:  python debug_build_index.py
import os, pathlib, re, sys, requests, textwrap
from typing import List
from bs4 import BeautifulSoup
from chromadb import PersistentClient
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.core import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from dotenv import load_dotenv
import openai, numpy as np
load_dotenv(override=True)
# -------- paths --------

ROOT         = pathlib.Path(__file__).parent
PERSIST_DIR  = ROOT / "chroma_db"
RAW_HTML_DIR = ROOT / "html";  RAW_HTML_DIR.mkdir(exist_ok=True)

# -------- sanity checks --------
key = os.getenv("OPENAI_API_KEY")
if not key:
    sys.exit("❌  OPENAI_API_KEY is NOT set – export it or put it in .env first.")
openai.api_key = key
print("✅  Using OPENAI_API_KEY =", key[:10], "...")

# -------- URLs to index --------
URLS: List[str] = [
    "https://www.nhs.uk/conditions/migraine/",
    "https://www.nhs.uk/conditions/type-2-diabetes/",
    "https://www.cancerresearchuk.org/about-cancer/cancer-symptoms",
]

def fetch(url: str) -> pathlib.Path:
    fname = RAW_HTML_DIR / (re.sub(r"[^a-z0-9]+", "_", url.lower().split("//")[1]) + ".html")
    if not fname.exists():
        print("⇢ Downloading", url)
        fname.write_text(requests.get(url, timeout=20).text, encoding="utf-8")
    return fname

def html_to_text(p: pathlib.Path) -> str:
    soup = BeautifulSoup(p.read_text(encoding="utf-8"), "lxml")
    for t in soup(["nav", "footer", "aside", "script", "style"]): t.decompose()
    return soup.get_text(" ", strip=True)

# -------- build & persist --------
docs = [Document(text=html_to_text(fetch(u)), metadata={"source": u}) for u in URLS]
print("✓  Parsed", len(docs), "documents")

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

client     = PersistentClient(path=str(PERSIST_DIR))
collection = client.get_or_create_collection("nhs_docs")
store      = ChromaVectorStore(chroma_collection=collection, stores_text=True)

print("⇢ Embedding + upserting …"); sys.stdout.flush()
# index = VectorStoreIndex.from_documents(docs, vector_store=store, show_progress=True)
storage_ctx = StorageContext.from_defaults(vector_store=store)
index = VectorStoreIndex.from_documents(
    docs,
    storage_context=storage_ctx,
    show_progress=True,
)

# show how many docs Chroma *thinks* it has right now
print("Collection count *before* persist:", collection.count())

index.storage_context.persist(persist_dir=str(PERSIST_DIR))
print("✅  Persisted to", PERSIST_DIR)

# verify after re‑opening
recheck = PersistentClient(path=str(PERSIST_DIR))\
            .get_or_create_collection("nhs_docs").count()
print("Collection count *after* reopen :", recheck)
