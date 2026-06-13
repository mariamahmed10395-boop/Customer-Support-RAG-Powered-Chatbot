<div align="center">
🎯 Customer Support RAG + Power BI
AI-Powered Customer Support with Real-Time Analytics Dashboard
https://python.org
https://openai.com
https://powerbi.microsoft.com
LICENSE
</div>
📋 Table of Contents

    Overview
    Features
    Architecture
    Project Structure
    Quick Start
    Usage
    API Reference
    Configuration
    Development
    Roadmap

🔍 Overview
A Retrieval-Augmented Generation (RAG) system that transforms raw customer support data into intelligent, context-aware AI responses. Integrated with Power BI for real-time analytics and performance monitoring.

    💡 Why RAG? Combines the creativity of LLMs with the accuracy of your private knowledge base — no hallucinations, just facts.

✨ Features
Table
Feature Description Status
🤖 AI Chatbot Context-aware responses powered by RAG ✅ Active
🔍 Smart Retrieval FAISS/ChromaDB vector search ✅ Active
⚡ Embedding Cache Pre-computed vectors for instant startup ✅ Active
💻 Web Interface Clean, responsive chat UI ✅ Active
📊 Power BI Dashboard Real-time support analytics ✅ Active
🔄 Auto-Preprocessing Data cleaning & intelligent chunking ✅ Active
🏗️ Architecture
plain

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Data Sources │────▶│ Preprocessing │────▶│ Vector Storage │
│ (CSV, APIs...) │ │ (Clean, Chunk) │ │ (FAISS/Chroma) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│
▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Power BI │◀────│ Analytics │◀────│ LLM Engine │
│ Dashboard │ │ & Metrics │ │ (GPT + RAG) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
▲
│
┌─────────────────┐
│ Web Chat UI │
│ (User Queries) │
└─────────────────┘

Data Flow
Mermaid
Code Preview
Raw CSVPreprocessChunk & EmbedVector IndexUser QueryEmbed QueryRetrieve Top-KLLM + ContextResponsePower BI
📁 Project Structure
plain

Customer-Support-RAG-PowerBI/
│
├── 📂 Data/
│ └── customer_support_data.csv # Raw support tickets & FAQs
│
├── 📂 Data_Preprocessing/
│ ├── pipeline.py # ETL orchestration
│ └── preprocess.py # Text cleaning & chunking
│
├── 📂 embeddings_cache/
│ ├── embeddings.npy # Serialized vectors
│ ├── faiss.index # Fast similarity index
│ └── meta.json # ID-to-document mapping
│
├── 📂 static/ # 🎨 Frontend Assets
│ ├── app.js # Chat logic & API calls
│ ├── index.html # Main interface
│ └── styles.css # Custom styling
│
├── 📂 vector_store/ # 🔧 Backend Core
│ ├── build_chroma.py # ChromaDB builder
│ ├── test_retrieval.py # Retrieval QA tests
│ └── app.py # Flask/FastAPI server
│
├── .gitignore
└── README.md # 📖 You are here

🚀 Quick Start
Prerequisites

    Python 3.8+
    OpenAI API key
    Power BI Desktop (optional, for analytics)

1. Clone & Install
   bash

git clone https://github.com/yourusername/Customer-Support-RAG-PowerBI.git
cd Customer-Support-RAG-PowerBI

# Create virtual environment

python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies

pip install -r requirements.txt

2. Configure Environment
   bash

# .env file

OPENAI_API_KEY=sk-your-key-here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-3.5-turbo
TOP_K_RETRIEVAL=5
CHUNK_SIZE=512
CHUNK_OVERLAP=50

3. Prepare Data
   bash

# Place your CSV in Data/ then run:

python Data_Preprocessing/pipeline.py

# Build vector index

python vector_store/build_chroma.py

4. Launch 🚀
   bash

python vector_store/app.py

    Open: http://localhost:5000

🖥️ Usage
💬 Web Chat Interface
bash

# Start the server

python vector_store/app.py

Navigate to http://localhost:5000 — start chatting with your AI support agent.
🔍 Test Retrieval
bash

# Interactive testing

python vector_store/test_retrieval.py

# Single query test

python vector_store/test_retrieval.py --query "How do I reset my password?"

📊 Power BI Dashboard

    Open Power BI Desktop
    Get Data → Web or CSV
    Connect to your API endpoint or export data
    Load the template: dashboard/customer_support.pbix

📡 API Reference
Endpoints
Table
Method Endpoint Description Payload
GET / Chat UI —
POST /api/chat Ask question {"query": "..."}
GET /api/health Health check —
GET /api/stats Support metrics —
Example Request
bash

curl -X POST http://localhost:5000/api/chat \
 -H "Content-Type: application/json" \
 -d '{
"query": "How do I track my order?",
"session_id": "user_123"
}'

Example Response
JSON

{
"answer": "You can track your order by visiting the 'Orders' section...",
"sources": [
{"id": "doc_42", "score": 0.94, "snippet": "..."}
],
"confidence": 0.92,
"response_time_ms": 340
}

⚙️ Configuration
Table
Parameter File Default Description
CHUNK_SIZE preprocess.py 512 Tokens per document chunk
CHUNK_OVERLAP preprocess.py 50 Overlap between chunks
TOP_K app.py 5 Retrieved documents per query
TEMPERATURE app.py 0.3 LLM creativity (0-1)
MAX_TOKENS app.py 512 Max response length
EMBEDDING_MODEL build_chroma.py text-embedding-3-small OpenAI embedding model
🛠️ Development
Running Tests
bash

# Test retrieval accuracy

pytest tests/test_retrieval.py -v

# Test API endpoints

pytest tests/test_api.py -v

Rebuilding the Knowledge Base
bash

# Clean old embeddings

rm -rf embeddings_cache/\*

# Re-run pipeline

python Data_Preprocessing/pipeline.py
python vector_store/build_chroma.py

Adding Custom Data

    Add CSV to Data/customer_support_data.csv
    Ensure columns: question, answer, category, priority
    Rebuild index (see above)

🗺️ Roadmap

    [x] Core RAG pipeline
    [x] Web chat interface
    [x] Power BI integration
    [x] FAISS + ChromaDB support
    [ ] 🌐 Multi-language support (Q3 2026)
    [ ] 💬 Conversation history & context (Q3 2026)
    [ ] 👍 User feedback loop (Q4 2026)
    [ ] 🔗 Teams/Slack integration (Q4 2026)
    [ ] 🧠 Fine-tuned domain model (2027)

🧰 Tech Stack

<div align="center">
Table
Layer	Technology
Vector DB	FAISS · ChromaDB
Embeddings	OpenAI text-embedding-3
LLM	OpenAI GPT / Azure OpenAI
Backend	Flask / FastAPI
Frontend	Vanilla JS · HTML5 · CSS3
Analytics	Microsoft Power BI
Data	Pandas · NumPy · CSV
</div>
🤝 Contributing

    Fork the repository
    Create a feature branch: git checkout -b feature/amazing-feature
    Commit changes: git commit -m 'Add amazing feature'
    Push to branch: git push origin feature/amazing-feature
    Open a Pull Request

📄 License
Distributed under the MIT License. See LICENSE for details.

<div align="center">
⬆ Back to Top
Built with ❤️ for better customer experiences
</div>
