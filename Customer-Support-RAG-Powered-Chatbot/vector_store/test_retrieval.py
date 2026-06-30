from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma(
    persist_directory="chroma_db_store",
    embedding_function=embedding
)

results = db.similarity_search("إرجاع المنتج")

for r in results:
    print(r.page_content)
