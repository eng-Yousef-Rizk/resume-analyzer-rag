import os
import json
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH, override=True, encoding="utf-8-sig")

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError(
        f"GROQ_API_KEY not found. Looked for .env at: {ENV_PATH} "
        f"(exists: {ENV_PATH.exists()}). Expected a line like GROQ_API_KEY=gsk_..."
    )

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from groq import Groq

from vector_db.vector_store import get_conn, load_all
from vector_db.vector_search import cosine_top_k

from Backend.db_setup import init_all_tables
from Backend.jobs_router import router as jobs_router
from Backend.auth_router import router as auth_router
from Backend import resume_router as rr
from Backend.recommend_router import router as recommend_router

app = FastAPI()

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_NAME = "openai/gpt-oss-20b"

embed_model = SentenceTransformer(EMBED_MODEL_NAME)
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

conn = get_conn()
ids, texts, matrix = load_all(conn)
print(f"loaded {len(ids)} chunks into memory")


class AnalyzeRequest(BaseModel):
    resume_text: str


SYSTEM_PROMPT = """You are an expert resume reviewer.
Use the provided context (hiring qualifications, best practices, guidelines) to analyze the candidate's resume.
Respond ONLY with a JSON object matching this exact schema:
{
  "overall_score": <integer 1-10>,
  "strengths": [<string>, ...],
  "weaknesses": [<string>, ...],
  "suggestions": [<string>, ...]
}
No text outside the JSON object."""


def retrieve_context(text: str) -> str:
    vec = embed_model.encode(text)
    top = cosine_top_k(vec, matrix, k=5)
    return "\n\n".join(texts[idx] for idx, _score in top)


@app.post("/analyze")
def analyze_resume(req: AnalyzeRequest):
    context = retrieve_context(req.resume_text)

    user_prompt = f"""Context (hiring criteria & best practices):
{context}

Candidate's resume:
{req.resume_text}

Analyze this resume based on the context above."""

    response = groq_client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


init_all_tables()
rr.kb_retriever = retrieve_context

app.include_router(jobs_router)
app.include_router(auth_router)
app.include_router(rr.router)
app.include_router(recommend_router)

# لازم يفضل آخر سطر في الملف، بعد كل الـ routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")