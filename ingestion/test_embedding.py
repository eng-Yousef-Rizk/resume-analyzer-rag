from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = [
    "5 years of experience in Python backend development",
    "Senior developer skilled in Python and Django",
    "I love cooking pasta on weekends"
]

embeddings = model.encode(sentences)

print(embeddings.shape)
print(embeddings[0][:5])  # أول 5 أرقام من أول vector