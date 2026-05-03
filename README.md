# Customer Support RAG‑Powered Intelligent Chatbot

A production‑ready support automation system using Retrieval‑Augmented Generation (RAG) and vector search. It serves real customer queries and integrates with business backend systems.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Milestone 1: Data Collection & Preprocessing](#milestone-1-data-collection--preprocessing)
- [Milestone 2: Model Development & Evaluation](#milestone-2-model-development--evaluation)
- [Milestone 3: Advanced Techniques & Azure Deployment](#milestone-3-advanced-techniques--azure-deployment)
- [Milestone 4: MLOps & Monitoring](#milestone-4-mlops--monitoring)
- [Milestone 5: Final Documentation & Presentation](#milestone-5-final-documentation--presentation)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [License](#license)

---

## Project Overview

This project builds a production‑ready customer support chatbot powered by **Retrieval‑Augmented Generation (RAG)**. The system retrieves relevant context from support tickets, FAQs, and product documentation, then generates accurate, context‑aware responses using a Large Language Model (LLM).

**Key Capabilities:**

- 🔍 **Intelligent Retrieval** — Semantic search across knowledge bases using FAISS + ChromaDB dual vector stores
- 🤖 **Context‑Aware Generation** — LLM responses grounded in retrieved documents
- 🌐 **REST API** — FastAPI/Flask backend with OpenAPI documentation
- 🎨 **Web Interface** — Vanilla JS frontend for real‑time chat interactions
- ☁️ **Azure‑Ready** — Containerized for Azure App Service / Azure ML deployment
- 📊 **MLOps** — Experiment tracking, monitoring, and automated retraining pipelines

---

## Architecture

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ User Query │────▶│ REST API │────▶│ Query Embedding │
│ (Web / API) │ │ (app.py) │ │ (SentenceTransformer)
└─────────────────┘ └─────────────────┘ └─────────────────┘
│
┌───────────────────────────┘
▼
┌─────────────────┐
│ Vector Search │
│ FAISS Index │
│ ChromaDB │
└─────────────────┘
│
▼
┌─────────────────┐
│ Retrieved │
│ Chunks + Meta │
│ (meta.json) │
└─────────────────┘
│
▼
┌─────────────────┐ ┌─────────────────┐
│ LLM Prompt │────▶│ Response Gen │
│ (Context + Q) │ │ (HuggingFace/ │
└─────────────────┘ │ OpenAI/Azure) │
└─────────────────┘

---

## Project Structure

Customer-Support-RAG-Powered-Chatbot/
│
├── Data/
│ └── customer_support_data.csv # Raw support tickets, FAQs, docs
│
├── Data_Preprocessing/
│ ├── pycache/
│ ├── pipeline.py # End-to-end preprocessing orchestrator
│ └── preprocess.py # Text cleaning, chunking, normalization
│
├── embeddings_cache/
│ ├── embeddings.npy # Precomputed vector embeddings (NumPy)
│ ├── faiss.index # FAISS index for fast ANN search
│ └── meta.json # Metadata mapping: index → document chunk
│
├── static/ # Frontend assets
│ ├── index.html # Chat UI (vanilla HTML)
│ ├── styles.css # Responsive styling
│ └── app.js # Frontend logic, API calls, chat history
│
├── vector_store/
│ ├── build_chroma.py # ChromaDB vector store builder
│ └── test_retrieval.py # Retrieval accuracy & performance tests
│
├── app.py # Main backend server (FastAPI/Flask)
├── .gitignore
└── README.md # This file

---

## Milestone 1: Data Collection & Preprocessing

### Objectives

- Aggregate support ticket logs, FAQs, documentation, and knowledge base articles
- Build a clean, unified text corpus ready for embedding and retrieval

### Tasks

#### 1. Data Ingestion

- **Source:** `Data/customer_support_data.csv`
- Collect historical support tickets, product manuals, FAQ entries, and agent responses
- Supports CRM integrations (Zendesk, ServiceNow, Jira Service Management)

#### 2. Preprocessing

Run the preprocessing pipeline:

```bash
cd Data_Preprocessing
python pipeline.py

preprocess.py handles:

    * Text Cleaning: HTML stripping, Unicode normalization, deduplication
    * Noise Removal: Email signatures, timestamps, system metadata, PII redaction
    * Tokenization: Sentence/paragraph-aware chunking optimized for retrieval
    * Quality Checks: Empty document filtering, length validation, language detection

3. Exploratory Data Analysis (EDA)

   *  Analyze common query patterns and topic distributions
   *  Evaluate response effectiveness (resolution time, CSAT, escalation rates)
   * Identify knowledge gaps and high‑frequency issue clusters

Deliverables

| Deliverable                    | Artifact                                           |
| ------------------------------ | -------------------------------------------------- |
| **Processed Text Corpus**      | `Data_Preprocessing/` output → chunked documents   |
| **Preprocessing Pipeline Doc** | `Data_Preprocessing/pipeline.py` + `preprocess.py` |
| **Support Data EDA Report**    | Run analysis on `Data/customer_support_data.csv`   |


Milestone 2: Model Development & Evaluation
Objectives

    * Train and evaluate a RAG retrieval + generation pipeline
    * Ensure high relevance, accuracy, and fluency of generated responses

Tasks
1. Model Building
Embedding Generation
Precomputed embeddings are cached in embeddings_cache/:

    * embeddings.npy — NumPy array of document embeddings (SentenceTransformers / OpenAI)
    * faiss.index — FAISS flat/IP index for approximate nearest neighbor search
    * meta.json — Metadata mapping indices to original document chunks, sources, and timestamps

Vector Store Setup
Option A: FAISS (Local, Fast)
Already configured via embeddings_cache/faiss.index. Ideal for single‑node deployments and prototyping.
Option B: ChromaDB (Persistent, Queryable)

cd vector_store
python build_chroma.py


ChromaDB provides persistent storage, metadata filtering, and hybrid search capabilities.
RAG Pipeline Configuration
The backend (app.py) orchestrates:

    1. Query Embedding — Convert user query to dense vector
    2. Retrieval — FAISS / Chroma similarity search → top‑k relevant chunks
    3. Augmentation — Inject retrieved context into LLM prompt
    4. Generation — LLM produces grounded, citation‑aware response

2. Evaluation

Run retrieval and generation tests:

cd vector_store
python test_retrieval.py

Metrics:

| Category   | Metric                          | Target  |
| ---------- | ------------------------------- | ------- |
| Retrieval  | Hit Rate @k                     | > 0.90  |
| Retrieval  | MRR (Mean Reciprocal Rank)      | > 0.85  |
| Retrieval  | NDCG @k                         | > 0.88  |
| Generation | BLEU                            | > 0.40  |
| Generation | ROUGE‑L                         | > 0.45  |
| End‑to‑End | Answer Relevance (LLM‑as‑judge) | > 4.0/5 |
| End‑to‑End | Hallucination Rate              | < 5%    |

3. Optimization

    * Chunk Size Tuning: 200‑500 tokens for support docs; 100‑200 for chat logs
    * Re‑ranking: Cross‑encoder or Cohere Rerank for second‑stage ranking
    * Hybrid Search: Combine dense embeddings + BM25 keyword search
    * Prompt Engineering: Few‑shot examples, system prompts for support tone

Deliverables

| Deliverable                 | Artifact                                                |
| --------------------------- | ------------------------------------------------------- |
| **Trained RAG Pipeline**    | `app.py` + `embeddings_cache/` + `vector_store/`        |
| **Model Evaluation Report** | Output from `test_retrieval.py` + generation benchmarks |

Milestone 3: Advanced Techniques & Azure Deployment
Objectives

    * Deploy the intelligent chatbot as a production support service
    * Ensure scalability, security, and seamless integration

Tasks
1. Azure Integration
Containerization

# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]


Deployment Options:

| Service                   | Use Case                 | Command                 |
| ------------------------- | ------------------------ | ----------------------- |
| Azure App Service         | Simple web app hosting   | `az webapp up --sku B3` |
| Azure Container Apps      | Serverless containers    | `az containerapp up`    |
| Azure ML Managed Endpoint | ML model serving         | Azure ML SDK v2         |
| AKS                       | Kubernetes orchestration | Helm charts in `infra/` |

Vector Database in Azure:

    * Azure Cognitive Search — Native vector search with hybrid retrieval
    * Azure Cosmos DB for MongoDB vCore — Vector search via $vectorSearch
    * Azure AI Search — Enterprise‑grade semantic ranking

2. API & Workflow Integration

REST API Endpoints:

| Endpoint    | Method | Description                         | Auth               |
| ----------- | ------ | ----------------------------------- | ------------------ |
| `/chat`     | POST   | Main RAG chat endpoint              | API Key / Azure AD |
| `/health`   | GET    | Service health & dependency checks  | Public             |
| `/feedback` | POST   | Submit thumbs up/down for responses | API Key            |
| `/search`   | POST   | Raw retrieval (chunks only)         | API Key            |

Workflow Integrations:

* Support portal embed (Zendesk, Salesforce, custom CRM)
* Auto‑ticket creation on unresolved queries
* Agent handoff with full context transfer
* WebSocket support for real‑time streaming responses

3. Security & Access

| Layer          | Implementation                                      |
| -------------- | --------------------------------------------------- |
| Authentication | Azure Entra ID (SSO), API Keys                      |
| Authorization  | RBAC roles (admin, agent, end‑user)                 |
| Network        | Private Endpoints, VNet integration                 |
| Secrets        | Azure Key Vault (connection strings, API keys)      |
| Data           | Encryption at rest (AES‑256) + in transit (TLS 1.3) |
| Compliance     | Audit logging, data residency, GDPR/CCPA ready      |

Deliverables

| Deliverable                    | Artifact                             |
| ------------------------------ | ------------------------------------ |
| **Deployed Chatbot Service**   | Live endpoint with health checks     |
| **Integration & Security Doc** | `infra/` Terraform/Bicep + API specs |

Milestone 4: MLOps & Monitoring

Objectives

    Track performance continuously and automate retraining
    Maintain model quality and system reliability over time

Tasks
1. Experiment Tracking
Use MLflow (Azure ML integration or self‑hosted) to track:

    RAG configurations: embedding models, chunk sizes, top‑k, temperature
    Prompt versions and few‑shot template iterations
    Evaluation metrics across A/B experiments
    Model registry: dev → staging → production promotion gates

2. Monitoring
Operational Metrics (Azure Monitor + Application Insights):

| Metric              | Target  | Alert Threshold |
| ------------------- | ------- | --------------- |
| P50 Latency         | < 500ms | > 1s            |
| P95 Latency         | < 2s    | > 3s            |
| P99 Latency         | < 5s    | > 8s            |
| Error Rate          | < 0.1%  | > 1%            |
| Token Usage / Query | Track   | Budget alert    |


Quality Metrics:

    Retrieval precision (manual + automated checks)
    Answer relevance scores (LLM‑as‑judge)
    User satisfaction: Thumbs up/down via /feedback
    CSAT / NPS correlation with chatbot interactions

Dashboards: Grafana or Azure Dashboards with real‑time KPIs
3. Retraining Mechanism

# Manual refresh
python Data_Preprocessing/pipeline.py      # Reprocess data
python vector_store/build_chroma.py          # Rebuild embeddings

Automated Pipeline:

    Scheduled: Weekly cron job for knowledge base refresh
    Trigger‑based: Retrain when accuracy < threshold or new product release
    Feedback Loop: Incorporate corrected answers and user feedback into training corpus
    CI/CD: GitHub Actions / Azure DevOps for testing → staging → production

Deliverables

| Deliverable              | Artifact                                  |
| ------------------------ | ----------------------------------------- |
| **Monitoring Dashboard** | Azure Monitor / Grafana dashboards        |
| **Retraining Pipeline**  | `pipeline.py` → `build_chroma.py` + CI/CD |

Milestone 5: Final Documentation & Presentation
Deliverables

| Deliverable                      | Contents                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------- |
| **Final Report**                 | Architecture decisions, performance benchmarks, lessons learned, security audit |
| **Demo Presentation**            | Live walkthrough: `static/index.html` → API → RAG pipeline → response           |
| **Business KPI Impact Analysis** | Ticket deflection %, AHT reduction, CSAT delta, cost per query, ROI             |

Getting Started
Prerequisites

    Python 3.10+
    pip package manager
    (Optional) Azure CLI + subscription for cloud deployment
'''
# Clone repository
git clone https://github.com/mariamahmed10395-boop/Customer-Support-RAG-Powered-Chatbot.git
cd customer-support-rag-chatbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and Azure credentials
'''
Running Locally:

'''
# 1. Preprocess data (one-time or on data update)
cd Data_Preprocessing
python pipeline.py

# 2. Build vector store (if using ChromaDB)
cd ../vector_store
python build_chroma.py

# 3. Start backend server
cd ..
python app.py

# 4. Open frontend
# Navigate to http://localhost:8000 or open static/index.html
'''

Running Tests

'''
# Retrieval accuracy tests
cd vector_store
python test_retrieval.py

# Full test suite
pytest tests/ -v --cov=src
'''
🔧 Component Reference

| File                               | Purpose                                               | Key Dependencies               |
| ---------------------------------- | ----------------------------------------------------- | ------------------------------ |
| `app.py`                           | Main ASGI/WSGI server, API routes, RAG orchestration  | FastAPI/Flask, Uvicorn         |
| `Data_Preprocessing/pipeline.py`   | End‑to‑end data flow: load → clean → chunk → validate | Pandas, NLTK, spaCy            |
| `Data_Preprocessing/preprocess.py` | Text utilities: cleaners, chunkers, normalizers       | Regex, BeautifulSoup           |
| `vector_store/build_chroma.py`     | ChromaDB initialization and document ingestion        | ChromaDB, SentenceTransformers |
| `vector_store/test_retrieval.py`   | Benchmark retrieval accuracy and latency              | FAISS, pytest                  |
| `static/index.html`                | Chat interface markup                                 | Vanilla HTML5                  |
| `static/app.js`                    | Frontend: WebSocket/REST API, chat history, rendering | Fetch API, DOM                 |
| `static/styles.css`                | Responsive layout, dark/light mode, animations        | CSS3                           |
| `embeddings_cache/embeddings.npy`  | Serialized embedding matrix                           | NumPy                          |
| `embeddings_cache/faiss.index`     | Binary FAISS index for ANN                            | FAISS‑cpu/gpu                  |
```
