import numpy as np


def cosine_top_k(query_vec, chunk_vecs, k=3):
    """
    query_vec:  shape (384,)      <- the question's vector
    chunk_vecs: shape (150, 384)  <- the vectors of all chunks
    returns:    list of (index, score) for the top k results, sorted from highest to lowest
    """
    # TODO 1: normalize both so every vector has length 1
    query_vec_len = np.linalg.norm(query_vec, axis=0)
    chunk_vecs_len = np.linalg.norm(chunk_vecs, axis=1, keepdims=True)
    query_vec_normalized = query_vec / query_vec_len
    chunk_vecs_normalized = chunk_vecs / chunk_vecs_len

    # TODO 2: one score per chunk, no for loop -> shape (n_chunks,)
    score = np.dot(chunk_vecs_normalized, query_vec_normalized)

    # TODO 3: indices of the top k scores, best first
    top_indices = np.argsort(score)[::-1][:k]

    # TODO 4: (index, score) tuples as plain Python types (safe for JSON later)
    return [(int(i), float(score[i])) for i in top_indices]


if __name__ == "__main__":
    # quick self-test: بيشتغل بس لما تشغل الملف مباشرة
    rng = np.random.default_rng(0)
    chunk_vecs = rng.normal(size=(150, 384))

    results = cosine_top_k(chunk_vecs[10], chunk_vecs, k=3)
    print(results)

    assert results[0][0] == 10, "chunk 10 should retrieve itself first"
    assert abs(results[0][1] - 1.0) < 1e-6, "self-similarity should be ~1.0"
    assert results[0][1] >= results[1][1] >= results[2][1], "scores must be descending"
    print("all checks passed")