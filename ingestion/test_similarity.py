from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = [
    "5 years of experience in Python backend development",
    "Senior developer skilled in Python and Django",
    "I love cooking pasta on weekends"
]

embeddings = model.encode(sentences)

sim_1_2 = util.cos_sim(embeddings[0], embeddings[1])
sim_1_3 = util.cos_sim(embeddings[0], embeddings[2])

print("Similarity (Python dev vs Django dev):", sim_1_2)
print("Similarity (Python dev vs cooking):", sim_1_3)