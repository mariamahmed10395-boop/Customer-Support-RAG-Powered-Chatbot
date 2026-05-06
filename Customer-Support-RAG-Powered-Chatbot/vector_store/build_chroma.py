import pandas as pd
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
docs = [
    Document(page_content="سياسة الإرجاع خلال 24 ساعة"),
    Document(page_content="يمكن استبدال المنتج خلال 7 أيام")
]

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma.from_documents(
    docs,
    embedding,
    persist_directory="chroma_db_store"
)

db.persist()

print("done")
