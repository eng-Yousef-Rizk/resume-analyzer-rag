from pathlib import Path
from sentence_transformers import SentenceTransformer

from ingestion.chunker import load_kb_directory
from vector_db.vector_store import get_conn, init_table, add_chunk

MODEL_NAME = "all-MiniLM-L6-v2"   # 384 dims
KB_DIR = Path(__file__).resolve().parent.parent / "kb"


def build_index():
    model = SentenceTransformer(MODEL_NAME)
    conn = get_conn()
    init_table(conn)
    conn.execute("DELETE FROM chunks")
    conn.commit()

    chunks = load_kb_directory(str(KB_DIR))
    if not chunks:
        print(f"no chunks found in {KB_DIR}")
        return

    texts = [c["text"] for c in chunks]
    sources = [c["source"] for c in chunks]

    print(f"embedding {len(texts)} chunks...")
    vectors = model.encode(texts)

    for source, text, vec in zip(sources, texts, vectors):
        add_chunk(conn, source, text, vec)

    print(f"indexed {len(texts)} chunks from {len(set(sources))} files")


if __name__ == "__main__":
    build_index()