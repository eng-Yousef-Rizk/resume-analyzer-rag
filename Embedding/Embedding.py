import json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

with open(r"D:\ITI\Final Project\kb_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

# TODO: Extract a list containing only the text from each item in chunks
texts = [item["text"] for item in chunks]

# حول كل الـ texts لـ embeddings دفعة واحدة (batch)
embeddings = model.encode(texts, show_progress_bar=True)

print("Number of chunks:", len(chunks))
print("Embeddings shape:", embeddings.shape)
