import os
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(BASE_DIR, "embeddings_cache")

if not os.path.exists(os.path.join(cache_dir, "meta.json")):
    cache_dir = os.path.join(BASE_DIR, "Customer-Support-RAG-Powered-Chatbot", "embeddings_cache")

index = faiss.read_index(os.path.join(cache_dir, "faiss.index"))

with open(os.path.join(cache_dir, "meta.json"), "r", encoding="utf-8") as f:
    kb_data = json.load(f)
    
    if isinstance(kb_data, dict):
        meta_data = kb_data.get("embeddings", [])
    else:
        meta_data = kb_data

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

def get_relevant_context(query: str, k: int = 3):
    """
    بتاخد سؤال العميل وترجع أقرب إجابات وسياق مناسب من الداتا المنظفة
    """
    try:
        query_vector = model.encode([query], convert_to_numpy=True)
        distances, indices = index.search(query_vector, k)
        
        context_list = []
        for idx in indices[0]:
            if idx < len(meta_data):
                item = meta_data[idx]
                context_list.append(f"السؤال: {item['question']}\nالإجابة: {item['answer']}")
        
        return "\n\n".join(context_list)
    except Exception as e:
        print(f"Error in retrieval: {e}")
        return ""

if __name__ == "__main__":
    test_res = get_relevant_context("تأخير الشحن")
    print(test_res)