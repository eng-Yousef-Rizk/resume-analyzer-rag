import sqlite3
import numpy as np

DB_PATH = "resume_analyzer.db"   # عدّله لاسم الـ DB عندك
DIM = 384                        # لازم يطابق الـ embedding model
DTYPE = np.float32               # نفس النوع في الحفظ والقراءة، ماتغيروش


def get_conn(db_path=DB_PATH):
    return sqlite3.connect(db_path)


def init_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            source    TEXT NOT NULL,
            text      TEXT NOT NULL,
            embedding BLOB NOT NULL
        )
        """
    )
    conn.commit()


def add_chunk(conn, source, text, vec):
    vec = np.asarray(vec, dtype=DTYPE)
    if vec.shape != (DIM,):
        raise ValueError(f"expected shape ({DIM},), got {vec.shape}")

    cur = conn.execute(
        "INSERT INTO chunks (source, text, embedding) VALUES (?, ?, ?)",
        (source, text, vec.tobytes()),
    )
    conn.commit()
    return cur.lastrowid


def load_all(conn):
    """returns (ids, texts, matrix) — matrix shape (n_chunks, DIM)"""
    rows = conn.execute(
        "SELECT id, text, embedding FROM chunks ORDER BY id"
    ).fetchall()

    if not rows:
        return [], [], np.empty((0, DIM), dtype=DTYPE)

    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]
    matrix = np.stack([np.frombuffer(r[2], dtype=DTYPE) for r in rows])
    return ids, texts, matrix


if __name__ == "__main__":
    # self-test على DB في الذاكرة، مش بيلمس الـ DB الحقيقية
    # شغّله من فولدر المشروع بـ: python -m retrieval.vector_store
    from vector_search import cosine_top_k

    conn = sqlite3.connect(":memory:")
    init_table(conn)

    rng = np.random.default_rng(0)
    originals = rng.normal(size=(5, DIM)).astype(DTYPE)
    for i, v in enumerate(originals):
        add_chunk(conn, "test.pdf", f"chunk number {i}", v)

    ids, texts, matrix = load_all(conn)
    print(matrix.shape, matrix.dtype)          # (5, 384) float32
    assert np.allclose(matrix, originals)      # الحفظ والقراءة ما بوّظوش القيم

    results = cosine_top_k(originals[3], matrix, k=2)