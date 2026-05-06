"""
RAG (Retrieval-Augmented Generation) System for Customer Support Data
=====================================================================
Uses Sentence-BERT embeddings + FAISS for semantic similarity search
over 91K+ customer support Q&A pairs.
"""

import os
import sys
import json
import time
import hashlib
import numpy as np
import pandas as pd
import faiss
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --- Configuration -----------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "customer_support_data.csv")
CACHE_DIR = os.path.join(BASE_DIR, "embeddings_cache")
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
TOP_K_DEFAULT = 10
BATCH_SIZE = 512

# Global state
model = None
index = None
df = None
knowledge_base = None  # deduplicated entries used for the index
stats_cache = None


def get_data_hash(path):
    """Compute a fast hash of the CSV file to detect changes."""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        # Read first and last 1MB for speed
        hasher.update(f.read(1024 * 1024))
        f.seek(-min(1024 * 1024, os.path.getsize(path)), 2)
        hasher.update(f.read())
    return hasher.hexdigest()


def load_data():
    """Load and preprocess the customer support CSV."""
    global df
    print("[*] Loading CSV data...")
    start = time.time()
    df = pd.read_csv(DATA_PATH, encoding="utf-8")
    df.columns = df.columns.str.strip().str.lower()
    # Clean whitespace
    for col in ["instruction", "response", "category", "intent"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    # Drop rows with empty instructions
    df = df[df["instruction"].str.len() > 0].reset_index(drop=True)
    print(f"    [OK] Loaded {len(df):,} rows in {time.time()-start:.1f}s")
    return df


def build_knowledge_base(dataframe):
    """
    Deduplicate: group by (intent, instruction) to avoid near-identical
    entries flooding results. Keep the first response for each unique instruction.
    """
    global knowledge_base
    print("[*] Building knowledge base (deduplicating)...")
    start = time.time()
    kb = dataframe.drop_duplicates(subset=["instruction"], keep="first").reset_index(drop=True)
    knowledge_base = kb
    print(f"    [OK] Knowledge base: {len(kb):,} unique entries (from {len(dataframe):,}) in {time.time()-start:.1f}s")
    return kb


def load_or_build_embeddings(kb):
    """Load cached embeddings or generate fresh ones."""
    global model, index

    os.makedirs(CACHE_DIR, exist_ok=True)
    data_hash = get_data_hash(DATA_PATH)
    cache_meta_path = os.path.join(CACHE_DIR, "meta.json")
    cache_emb_path = os.path.join(CACHE_DIR, "embeddings.npy")
    cache_index_path = os.path.join(CACHE_DIR, "faiss.index")

    # Check if cache is valid
    cache_valid = False
    if os.path.exists(cache_meta_path):
        with open(cache_meta_path, "r") as f:
            meta = json.load(f)
        if (
            meta.get("data_hash") == data_hash
            and meta.get("model") == MODEL_NAME
            and meta.get("num_entries") == len(kb)
            and os.path.exists(cache_emb_path)
            and os.path.exists(cache_index_path)
        ):
            cache_valid = True

    # Load model
    print(f"[*] Loading Sentence-BERT model: {MODEL_NAME}...")
    model_start = time.time()
    model = SentenceTransformer(MODEL_NAME)
    print(f"    [OK] Model loaded in {time.time()-model_start:.1f}s")

    if cache_valid:
        print("[*] Loading cached embeddings & FAISS index...")
        start = time.time()
        index = faiss.read_index(cache_index_path)
        print(f"    [OK] Cache loaded in {time.time()-start:.1f}s")
    else:
        print("[*] Generating embeddings (this may take a few minutes on first run)...")
        start = time.time()
        instructions = kb["instruction"].tolist()
        embeddings = model.encode(
            instructions,
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        embeddings = np.array(embeddings, dtype="float32")
        print(f"    [OK] Embeddings generated in {time.time()-start:.1f}s")

        # Build FAISS index
        print("[*] Building FAISS index...")
        idx_start = time.time()
        index = faiss.IndexFlatIP(EMBEDDING_DIM)
        index.add(embeddings)
        print(f"    [OK] FAISS index built in {time.time()-idx_start:.1f}s ({index.ntotal:,} vectors)")

        # Save cache
        print("[*] Saving cache to disk...")
        np.save(cache_emb_path, embeddings)
        faiss.write_index(index, cache_index_path)
        with open(cache_meta_path, "w") as f:
            json.dump(
                {
                    "data_hash": data_hash,
                    "model": MODEL_NAME,
                    "num_entries": len(kb),
                    "embedding_dim": EMBEDDING_DIM,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                f,
                indent=2,
            )
        print("    [OK] Cache saved!")


def compute_stats():
    """Compute and cache dataset statistics."""
    global stats_cache
    if df is None:
        return {}
    stats_cache = {
        "total_entries": int(len(df)),
        "unique_instructions": int(len(knowledge_base)) if knowledge_base is not None else 0,
        "categories": {k: int(v) for k, v in df["category"].value_counts().to_dict().items()},
        "intents": {k: int(v) for k, v in df["intent"].value_counts().to_dict().items()},
        "num_categories": int(df["category"].nunique()),
        "num_intents": int(df["intent"].nunique()),
    }
    return stats_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data, build embeddings, and prepare the search engine."""
    print("\n" + "=" * 60)
    print("  RAG Customer Support System -- Starting Up")
    print("=" * 60 + "\n")

    total_start = time.time()

    data = load_data()
    kb = build_knowledge_base(data)
    load_or_build_embeddings(kb)
    compute_stats()

    print(f"\n{'=' * 60}")
    print(f"  [OK] System ready in {time.time()-total_start:.1f}s")
    print(f"  [DATA] {len(data):,} total rows | {len(kb):,} indexed")
    print(f"  [FAISS] index: {index.ntotal:,} vectors ({EMBEDDING_DIM}d)")
    print(f"{'=' * 60}\n")
    yield
    print("Shutting down...")

# --- FastAPI App -------------------------------------------------------------
app = FastAPI(title="Customer Support RAG API", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
@app.get("/")
def home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
class SearchRequest(BaseModel):
    query: str
    category: str = "ALL"
    top_k: int = TOP_K_DEFAULT

@app.post("/api/search")
def search(request: SearchRequest):
    """Semantic search endpoint."""
    query = request.query.strip()
    category_filter = request.category.upper()
    top_k = min(request.top_k, 50)

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    start_time = time.time()

    # Encode query
    query_embedding = model.encode(
        [query], normalize_embeddings=True
    ).astype("float32")

    # If category filter, we search more candidates then filter
    search_k = top_k * 5 if category_filter != "ALL" else top_k

    # Search FAISS
    scores, indices = index.search(query_embedding, min(search_k, index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        row = knowledge_base.iloc[int(idx)]
        cat = row["category"]
        if category_filter != "ALL" and cat != category_filter:
            continue
        similarity = float(score) * 100  # Already cosine similarity
        results.append(
            {
                "instruction": str(row["instruction"]),
                "response": str(row["response"]),
                "category": str(cat),
                "intent": str(row["intent"]),
                "similarity": round(max(0, min(100, similarity)), 1),
            }
        )
        if len(results) >= top_k:
            break

    elapsed = time.time() - start_time

    return {
        "query": query,
        "category_filter": category_filter,
        "num_results": len(results),
        "search_time_ms": round(elapsed * 1000, 1),
        "results": results,
    }


@app.get("/api/categories")
def get_categories():
    """Return all categories with counts."""
    if df is None:
        return []
    cats = df["category"].value_counts().to_dict()
    return [{"name": k, "count": int(v)} for k, v in sorted(cats.items())]


@app.get("/api/stats")
def get_stats():
    """Return dataset statistics."""
    return stats_cache or compute_stats()


@app.get("/api/intents")
def get_intents(category: str = "ALL"):
    """Return all intents with counts, optionally filtered by category."""
    cat = category.upper()
    filtered = df if cat == "ALL" else df[df["category"] == cat]
    intents = filtered["intent"].value_counts().to_dict()
    return [{"name": k, "count": int(v)} for k, v in sorted(intents.items())]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
