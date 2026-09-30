from sentence_transformers import SentenceTransformer
from vector_db.vector_store import get_conn, load_all
from vector_db.vector_search import cosine_top_k

model = SentenceTransformer("all-MiniLM-L6-v2")
conn = get_conn()
ids, texts, matrix = load_all(conn)

print(f"loaded {len(ids)} chunks")

questions = [
    "What programming languages does the candidate know?",
    "Tell me about their work experience",
    "What is their education background?",
]

for q in questions:
    print(f"\n=== {q} ===")
    q_vec = model.encode(q)
    for idx, score in cosine_top_k(q_vec, matrix, k=3):
        print(f"{score:.3f} | {texts[idx][:150]}")