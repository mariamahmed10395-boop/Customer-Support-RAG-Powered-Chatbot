"""
RAG (Retrieval-Augmented Generation) System for Customer Support Data
=====================================================================
Uses Sentence-BERT embeddings + FAISS for semantic similarity search
over 24K+ unique customer support Q&A pairs.
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
knowledge_base = None  
stats_cache = None


def get_data_hash(path):
    """Compute a fast hash of the CSV file to detect changes."""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
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
    
    for col in ["instruction", "response", "category", "intent"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    df = df[df["instruction"].str.len() > 0].reset_index(drop=True)
    print(f"    [OK] Loaded {len(df):,} rows in {time.time()-start:.1f}s")
    return df


def build_knowledge_base(dataframe):
    """
    Deduplicate: group by unique instructions to avoid redundant entries
    flooding vector search results.
    """
    global knowledge_base
    print("[*] Building knowledge base (deduplicating)...")
    start = time.time()
    kb = dataframe.drop_duplicates(subset=["instruction"], keep="first").reset_index(drop=True)
    knowledge_base = kb
    print(f"    [OK] Knowledge base: {len(kb):,} unique entries (from {len(dataframe):,}) in {time.time()-start:.1f}s")
    return kb


def load_or_build_embeddings(kb):
    """Load cached embeddings or generate fresh ones via FAISS."""
    global model, index

    os.makedirs(CACHE_DIR, exist_ok=True)
    data_hash = get_data_hash(DATA_PATH)
    cache_meta_path = CACHE_DIR / "meta.json"
    cache_emb_path = CACHE_DIR / "embeddings.npy"
    cache_index_path = CACHE_DIR / "faiss.index"

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

        print("[*] Building FAISS index...")
        idx_start = time.time()
        index = faiss.IndexFlatIP(EMBEDDING_DIM)
        index.add(embeddings)
        print(f"    [OK] FAISS index built in {time.time()-idx_start:.1f}s ({index.ntotal:,} vectors)")

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
    """Compute and cache dataset metrics for Power BI and Frontend dashboards."""
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
    """Manage application startup and shutdown lifecycle events."""
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
    """Execute semantic query over FAISS vectors with on-the-fly translation for Arabic queries."""
    if model is None or index is None or knowledge_base is None:
        return []

    search_query = query.strip()

    # Detect if the query contains Arabic characters
    if any(u'\u0600' <= char <= u'\u06FF' for char in search_query):
        try:
            # Use Groq Llama-3 to translate the search query to English instantly
            translation_prompt = f"Translate the following customer support search query into a concise English search term. Return ONLY the translation, no explanation, no quotes:\n\n{search_query}"
            translation_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": translation_prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.0,
                max_tokens=50,
            )
            translated_text = translation_completion.choices[0].message.content.strip()
            print(f"[Translation Engine] Translated '{search_query}' -> '{translated_text}'")
            search_query = translated_text
        except Exception as e:
            print(f"[Translation Error] Failed to translate query: {e}")

    # Encode the final query (which is now in English)
    query_embedding = model.encode(
        [search_query], normalize_embeddings=True
    ).astype("float32")

    search_k = top_k * 5 if category_filter != "ALL" else top_k
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
            
        similarity = float(score) * 100  
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
    """Semantic search endpoint executing high-speed retrieval."""
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
    thread_id: str = "default_session"  


@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    Standard RAG Chat endpoint powered by LangGraph Workflow state machine.
    Features state persistence using MemorySaver checkpointers.
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


# --- STREAMING CHAT ENDPOINT -------------------------------------------------
class StreamChatRequest(BaseModel):
    query: str
    category: str = "ALL"
    top_k: int = 5


@app.post("/api/chat/stream")
async def chat_stream(request: StreamChatRequest):
    """
    Streaming RAG Chat endpoint emitting text/event-stream Server-Sent Events (SSE).
    Implements Cross-Lingual prompting strategies via Groq Llama-3 API.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if not groq_client:
        raise HTTPException(
            status_code=503,
            detail="Groq LLM service is not configured."
        )

    # Step 1: Execute fast synchronous FAISS retrieval
    top_k = min(request.top_k, 20)
    context_results = get_semantic_search_results(
        query, request.category.upper(), top_k
    )

    if context_results:
        context_block = "\n\n".join(
            f"Q: {r['instruction']}\nA: {r['response']}"
            for r in context_results
        )
    else:
        context_block = "No relevant documents were found in the knowledge base for this query."

    # Step 2: Formulate bilingual hardened RAG system prompt
    SYSTEM_PROMPT = """You are a precise, professional bilingual AI Assistant for the Customer Support RAG System.
Your ONLY source of truth is the "Retrieved Context" section provided below.

═══════════════════════════════════════════════════════
STRICT RAG GUARDRAIL RULES:
═══════════════════════════════════════════════════════
RULE 1 — LANGUAGE MATCHING & TRANSLATION:
- Detect the language of the user's question (Arabic or English).
- You MUST respond strictly in the SAME language the user used to ask their question.
- If the user writes in Arabic, you MUST review the provided English context, translate the facts accurately, and generate a natural, professional Arabic response.
- If the user writes in English, answer strictly in English.

RULE 2 — GROUNDING & NO HALLUCINATION:
- Answer EXCLUSIVELY using information found in the Retrieved Context below.
- Do NOT use any prior training knowledge or general world knowledge.
- NEVER invent facts, statistics, links, or customer support procedures.

RULE 3 — OUT-OF-DOMAIN REFUSAL:
- If the context does not contain the answer, politely inform the user in their language that you cannot assist with this request (e.g., "I'm sorry, I cannot find information regarding this request in the knowledge base.").

═══════════════════════════════════════════════════════
Retrieved Context (your ONLY allowed source of truth in English):
═══════════════════════════════════════════════════════
{context}
""".format(context=context_block)

    # Step 3: Define Async SSE Generator
    async def response_generator():
        try:
            loop = asyncio.get_event_loop()

            def _start_stream():
                return groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": query},
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.0,
                    max_tokens=1024,
                    stream=True,       
                )

            stream = await loop.run_in_executor(None, _start_stream)

            for chunk in stream:
                token = chunk.choices[0].delta.content
                if token is None:
                    continue

                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0)

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_payload = json.dumps({"error": str(e)})
            yield f"data: {error_payload}\n\n"
            yield "data: [DONE]\n\n"

    # Step 4: Dispatch StreamingResponse with strict SSE headers
    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/categories")
def get_categories():
    """Return all support categories with corresponding ticket counts."""
    if df is None:
        return []
    cats = df["category"].value_counts().to_dict()
    return [{"name": k, "count": int(v)} for k, v in sorted(cats.items())]


@app.get("/api/stats")
def get_stats():
    """Fetch global data processing and distribution statistics."""
    return stats_cache or compute_stats()


@app.get("/api/intents")
def get_intents(category: str = "ALL"):
    """Return customer intents filtered dynamically by category."""
    cat = category.upper()
    filtered = df if cat == "ALL" else df[df["category"] == cat]
    intents = filtered["intent"].value_counts().to_dict()
    return [{"name": k, "count": int(v)} for k, v in sorted(intents.items())]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)