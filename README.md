# 🎯 Customer Support RAG + Power BI

<div align="center">

### AI-Powered Customer Support with Real-Time Analytics Dashboard

Build an intelligent customer support assistant using **Retrieval-Augmented Generation (RAG)**, combined with **Power BI dashboards** for real-time analytics and performance monitoring.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT-green)
![PowerBI](https://img.shields.io/badge/PowerBI-Analytics-yellow)
![License](https://img.shields.io/badge/License-MIT-red)

</div>

---

## 📖 Overview

This project is an **AI-powered Customer Support Assistant** built using **Retrieval-Augmented Generation (RAG)**.

Instead of relying only on the LLM's memory, the system retrieves relevant information from your private knowledge base before generating responses, ensuring:

- ✅ Accurate answers with minimal hallucinations
- ✅ Context-aware customer support
- ✅ Fast semantic search using vector databases
- ✅ Real-time analytics through Power BI
- ✅ Easy integration with CSV files or APIs

> **Why RAG?**
>
> RAG combines the reasoning capabilities of Large Language Models with the reliability of your own data, giving you factual and trustworthy responses.

---

# ✨ Features

| Feature               | Description                            | Status |
| --------------------- | -------------------------------------- | ------ |
| 🤖 AI Chatbot         | Context-aware responses powered by RAG | ✅     |
| 🔍 Smart Retrieval    | Semantic search using FAISS / ChromaDB | ✅     |
| ⚡ Embedding Cache    | Pre-computed vectors for fast startup  | ✅     |
| 💻 Web Interface      | Clean and responsive chat UI           | ✅     |
| 📊 Power BI Dashboard | Real-time analytics & KPIs             | ✅     |
| 🔄 Auto Preprocessing | Data cleaning and intelligent chunking | ✅     |

---

# 🏗️ Architecture

```text
┌─────────────────┐
│ Data Sources    │
│ (CSV, APIs...)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Preprocessing   │
│ Clean + Chunk   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Storage  │
│ FAISS / Chroma  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Retrieval       │
│ Top-K Search    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM + RAG       │
│ GPT Responses   │
└────────┬────────┘
         │
   ┌─────┴─────┐
   ▼           ▼
Web Chat    Power BI
Interface   Dashboard
```

---

# 📂 Project Structure

```text
Customer-Support-RAG-PowerBI/

├── Data/
│   └── customer_support_data.csv

├── Data_Preprocessing/
│   ├── pipeline.py
│   └── preprocess.py

├── embeddings_cache/
│   ├── embeddings.npy
│   ├── faiss.index
│   └── meta.json

├── static/
│   ├── app.js
│   ├── index.html
│   └── styles.css

├── vector_store/
│   ├── build_chroma.py
│   ├── test_retrieval.py
│   └── app.py

├── tests/

├── .gitignore

└── README.md
```

---

# 🚀 Quick Start

## 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/Customer-Support-RAG-PowerBI.git

cd Customer-Support-RAG-PowerBI
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Configure Environment

Create a `.env` file:

```env
OPENAI_API_KEY=sk-your-key-here

EMBEDDING_MODEL=text-embedding-3-small

LLM_MODEL=gpt-4o-mini

TOP_K_RETRIEVAL=5

CHUNK_SIZE=512

CHUNK_OVERLAP=50
```

---

## 5️⃣ Prepare Data

Place your CSV file inside:

```text
Data/customer_support_data.csv
```

Then run:

```bash
python Data_Preprocessing/pipeline.py

python vector_store/build_chroma.py
```

---

## 6️⃣ Launch Application

```bash
python vector_store/app.py
```

Open:

```text
http://localhost:5000
```

---

# 💬 Usage

### Start Chat Server

```bash
python vector_store/app.py
```

Navigate to:

```text
http://localhost:5000
```

Start chatting with your AI customer support assistant.

---

### Test Retrieval

```bash
python vector_store/test_retrieval.py
```

Single query:

```bash
python vector_store/test_retrieval.py \
--query "How do I reset my password?"
```

---

# 📊 Power BI Dashboard

1. Open Power BI Desktop
2. Click **Get Data**
3. Select **CSV** or **Web API**
4. Connect to your exported data
5. Load:

```text
dashboard/customer_support.pbix
```

Monitor:

- Customer satisfaction
- Average response time
- Ticket categories
- Most common issues
- Agent performance

---

# 📡 API Reference

| Method | Endpoint      | Description       |
| ------ | ------------- | ----------------- |
| GET    | `/`           | Chat UI           |
| POST   | `/api/chat`   | Ask Question      |
| GET    | `/api/health` | Health Check      |
| GET    | `/api/stats`  | Analytics Metrics |

### Example Request

```bash
curl -X POST http://localhost:5000/api/chat \
-H "Content-Type: application/json" \
-d '{
  "query":"How do I track my order?",
  "session_id":"user_123"
}'
```

### Example Response

```json
{
  "answer": "You can track your order from the Orders section.",

  "sources": [
    {
      "id": "doc_42",
      "score": 0.94,
      "snippet": "..."
    }
  ],

  "confidence": 0.92,

  "response_time_ms": 340
}
```

---

# ⚙️ Configuration

| Parameter       | Default                |
| --------------- | ---------------------- |
| CHUNK_SIZE      | 512                    |
| CHUNK_OVERLAP   | 50                     |
| TOP_K           | 5                      |
| TEMPERATURE     | 0.3                    |
| MAX_TOKENS      | 512                    |
| EMBEDDING_MODEL | text-embedding-3-small |

---

# 🛠️ Development

### Run Tests

```bash
pytest tests/test_retrieval.py -v

pytest tests/test_api.py -v
```

### Rebuild Knowledge Base

```bash
rm -rf embeddings_cache/*

python Data_Preprocessing/pipeline.py

python vector_store/build_chroma.py
```

---

# 🗺️ Roadmap

- ✅ Core RAG Pipeline
- ✅ Web Chat Interface
- ✅ Power BI Integration
- ✅ FAISS Support
- ✅ ChromaDB Support
- ⏳ Multi-language Support
- ⏳ Conversation Memory
- ⏳ User Feedback Loop
- ⏳ Teams & Slack Integration
- ⏳ Fine-Tuned Domain Model

---

# 🧰 Tech Stack

| Layer           | Technology                |
| --------------- | ------------------------- |
| Vector Database | FAISS · ChromaDB          |
| Embeddings      | OpenAI text-embedding-3   |
| LLM             | GPT-4o / Azure OpenAI     |
| Backend         | Flask / FastAPI           |
| Frontend        | HTML5 · CSS3 · Vanilla JS |
| Analytics       | Microsoft Power BI        |
| Data Processing | Pandas · NumPy            |

---

# 🤝 Contributing

1. Fork the repository
2. Create a branch

```bash
git checkout -b feature/amazing-feature
```

3. Commit changes

```bash
git commit -m "Add amazing feature"
```

4. Push changes

```bash
git push origin feature/amazing-feature
```

5. Open a Pull Request

---

# 📄 License

Distributed under the **MIT License**.

See the `LICENSE` file for more information.

---

<div align="center">

### ⭐ If you like this project, give it a star!

Built with ❤️ to create better customer experiences.

</div>
