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
import asyncio
import numpy as np
import pandas as pd
import faiss
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from agent_brain.graph import customer_rag_graph


# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --- Configuration -----------------------------------------------------------
# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "Data" / "customer_support_data.csv"
CACHE_DIR = BASE_DIR / "embeddings_cache"
STATIC_DIR = BASE_DIR / "static"

MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_DIM = 768
TOP_K_DEFAULT = 10
BATCH_SIZE = 512

# Initialize Groq client securely
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = None
if GROQ_API_KEY and GROQ_API_KEY.strip():
    try:
        groq_client = Groq(api_key=GROQ_API_KEY.strip())
        print("[*] Groq Llama-3 client initialized successfully!")
    except Exception as e:
        print(f"[!] Failed to initialize Groq client: {e}")
else:
    print("[!] Warning: GROQ_API_KEY not set. Chat features will require setting the key in your .env file.")

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
    cache_meta_path = CACHE_DIR / "meta.json"
    cache_emb_path = CACHE_DIR / "embeddings.npy"
    cache_index_path = CACHE_DIR / "faiss.index"

    # Check if cache is valid
    cache_valid = False
    if cache_meta_path.exists():
        with open(cache_meta_path, "r") as f:
            meta = json.load(f)
        if (
            meta.get("data_hash") == data_hash
            and meta.get("model") == MODEL_NAME
            and meta.get("num_entries") == len(kb)
            and cache_emb_path.exists()
            and cache_index_path.exists()
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
        index = faiss.read_index(str(cache_index_path))
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
        faiss.write_index(index, str(cache_index_path))
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

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")

def get_semantic_search_results(query: str, category_filter: str = "ALL", top_k: int = TOP_K_DEFAULT):
    """Helper to query the FAISS index and return matching records."""
    if model is None or index is None or knowledge_base is None:
        return []

    # Encode query
    query_embedding = model.encode(
        [query], normalize_embeddings=True
    ).astype("float32")

    # If category filter, we search more candidates then filter
    search_k = top_k * 5 if category_filter != "ALL" else top_k

    # Search FAISS
    scores, indices = index.search(query_embedding, min(search_k, index.ntotal))

    results = []
    seen_intents = set()

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
            
        if score < 0.25:
            continue
            
        row = knowledge_base.iloc[int(idx)]
        
        intent = str(row["intent"])
        if intent in seen_intents:
            continue
        seen_intents.add(intent)
        
        cat = row["category"]
        if category_filter != "ALL" and cat != category_filter:
            continue
            
        similarity = float(score) * 100  # Already cosine similarity
        results.append(
            {
                "instruction": str(row["instruction"]),
                "response": str(row["response"]),
                "category": str(cat),
                "intent": intent,
                "similarity": round(max(0, min(100, similarity)), 1),
            }
        )
        if len(results) >= top_k:
            break
            
    return results

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
    results = get_semantic_search_results(query, category_filter, top_k)
    elapsed = time.time() - start_time

    return {
        "query": query,
        "category_filter": category_filter,
        "num_results": len(results),
        "search_time_ms": round(elapsed * 1000, 1),
        "results": results,
    }

class ChatRequest(BaseModel):
    query: str
    category: str = "ALL"
    top_k: int = 5
    thread_id: str = "default_session"  # ممرر هنا لربط الجلسات من الفرونت


@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    RAG Chat endpoint using the LangGraph Workflow from agent_brain/graph.py.
    Kept intact for backward compatibility with the PySide6 desktop client.
    """
    query = request.query.strip()
    category_filter = request.category.upper()
    top_k = min(request.top_k, 20)
    thread_id = request.thread_id.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if not groq_client:
        raise HTTPException(
            status_code=503,
            detail="Groq LLM service is not configured. Please add GROQ_API_KEY to your .env file."
        )

    try:
        graph_inputs = {"query": query, "messages": []}
        thread_config = {"configurable": {"thread_id": thread_id}}
        graph_output = customer_rag_graph.invoke(graph_inputs, config=thread_config)
        return {
            "query": query,
            "response": graph_output.get("response", ""),
            "transfer_to_human": graph_output.get("transfer_to_human", False),
            "thread_id": thread_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing LangGraph pipeline: {str(e)}"
        )


# ── STREAMING CHAT ENDPOINT ───────────────────────────────────────────────────
# This endpoint is consumed exclusively by the React frontend.
# It bypasses LangGraph and calls Groq directly with stream=True so that
# every token chunk is forwarded to the browser as a Server-Sent Event (SSE)
# the moment it arrives, producing the ChatGPT-style word-by-word effect.
# ─────────────────────────────────────────────────────────────────────────────

class StreamChatRequest(BaseModel):
    query: str
    category: str = "ALL"
    top_k: int = 5


@app.post("/api/chat/stream")
async def chat_stream(request: StreamChatRequest):
    """
    Streaming RAG Chat endpoint — returns text/event-stream.

    Flow:
      1. Retrieve top-k context chunks from FAISS (same helper as /api/search).
      2. Build the hardened RAG guardrail system prompt with the retrieved context.
      3. Call Groq chat completions with stream=True inside an async generator.
      4. Yield each token chunk as an SSE 'data:' line so the browser reader
         can append it to the active bot message in real time.
      5. Send a terminal 'data: [DONE]' event so the frontend knows the
         stream has ended and can finalise state.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if not groq_client:
        raise HTTPException(
            status_code=503,
            detail="Groq LLM service is not configured."
        )

    # ── Step 1: RAG Retrieval (runs synchronously — fast FAISS call) ──────────
    top_k = min(request.top_k, 20)
    context_results = get_semantic_search_results(
        query, request.category.upper(), top_k
    )

    # Build a compact context block from the retrieved Q-A pairs
    if context_results:
        context_block = "\n\n".join(
            f"Q: {r['instruction']}\nA: {r['response']}"
            for r in context_results
        )
    else:
        context_block = "No relevant documents were found in the knowledge base for this query."

    # ── Step 2: System prompt (strict RAG guardrail) ──────────────────────────
    SYSTEM_PROMPT = """You are a precise, professional AI Assistant for the CoreAI Knowledge Base system.
Your ONLY source of truth is the Retrieved Context provided below.

═══════════════════════════════════════════════════════
STRICT RAG GUARDRAIL RULES:
═══════════════════════════════════════════════════════
RULE 1 — GROUNDING: Answer EXCLUSIVELY from the Retrieved Context.
  Do NOT use prior training knowledge or general world knowledge.

RULE 2 — OUT-OF-DOMAIN REFUSAL: If the question cannot be answered
  from the context, respond with EXACTLY:
  "I cannot find any information regarding this in the uploaded CoreAI
  Knowledge Base documents. Currently, my knowledge is limited to the
  active files listed in your workspace panel."

RULE 3 — LANGUAGE MATCHING: Respond in the same language as the question.

RULE 4 — SOURCE CITATION: End successful answers with:
  📄 Source: [topic from context] | Confidence: [High/Medium/Low]

RULE 5 — NO HALLUCINATION: Never invent facts, statistics, or policies.
═══════════════════════════════════════════════════════
Retrieved Context (your ONLY allowed source of truth):
═══════════════════════════════════════════════════════
{context}
""".format(context=context_block)

    # ── Step 3: Async SSE generator ───────────────────────────────────────────
    async def response_generator():
        """
        Calls Groq with stream=True and yields one SSE 'data:' line per token.
        The Groq SDK returns a synchronous iterator even in streaming mode, so
        we run it in a thread pool executor to avoid blocking the event loop.
        """
        try:
            loop = asyncio.get_event_loop()

            # Build the Groq streaming call (synchronous SDK, runs in executor)
            def _start_stream():
                return groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": query},
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.0,
                    max_tokens=1024,
                    stream=True,       # <-- enables token-by-token streaming
                )

            # Kick off the stream in a thread so the async loop stays free
            stream = await loop.run_in_executor(None, _start_stream)

            # Iterate over each chunk the LLM sends back
            for chunk in stream:
                # Extract the token text from the delta (may be None on final chunk)
                token = chunk.choices[0].delta.content
                if token is None:
                    continue

                # Encode token as a JSON string to safely escape newlines/quotes,
                # then format as an SSE 'data:' line ending with double newline.
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"

                # Yield control back to the event loop between chunks so other
                # requests are not starved during a long generation.
                await asyncio.sleep(0)

            # ── Terminal event: signals the frontend reader to stop ────────────
            yield "data: [DONE]\n\n"

        except Exception as e:
            # Surface errors as a special SSE error event so the frontend
            # catch block can display the offline fallback message.
            error_payload = json.dumps({"error": str(e)})
            yield f"data: {error_payload}\n\n"
            yield "data: [DONE]\n\n"

    # ── Step 4: Return StreamingResponse ─────────────────────────────────────
    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",
        headers={
            # Prevent any proxy/CDN from buffering the SSE stream
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


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