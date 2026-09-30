import io, json
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pypdf import PdfReader
import docx
from Backend.auth_router import get_current_user
from Backend.db_setup import get_db
from Backend.llm import call_llm_json

router = APIRouter(prefix="/resume", tags=["resume"])

# main.py بيحط هنا دالة الـ retrieval بتاعة الـ RAG
kb_retriever = None

SYSTEM_PROMPT = """You are an expert resume reviewer. Analyze the resume and return ONLY a JSON object with exactly these keys:
{
  "summary": "2-3 sentence professional summary",
  "skills": ["..."],
  "education": [{"degree": "...", "institution": "...", "year": "..."}],
  "experience": [{"title": "...", "company": "...", "duration": "...", "highlights": ["..."]}],
  "overall_score": 0-100,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": ["..."],
  "missing_skills": ["..."],
  "recommended_certifications": ["..."],
  "learning_resources": [{"topic": "...", "resource": "..."}]
}
If a field is not found in the resume use an empty list or empty string. Do not invent facts.
Use the reference guidelines (if provided) to judge the resume and to write the strengths, weaknesses and suggestions."""

def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if name.endswith(".docx"):
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    raise HTTPException(400, "Only PDF or DOCX files are supported")

def analyze_text(text: str) -> dict:
    kb_context = kb_retriever(text) if kb_retriever else ""
    user_msg = f"Resume:\n{text[:12000]}"
    if kb_context:
        user_msg += f"\n\nReference guidelines:\n{kb_context}"
    return call_llm_json(SYSTEM_PROMPT, user_msg)

@router.post("/upload")
def upload_resume(file: UploadFile = File(...), user_id: int = Depends(get_current_user)):
    data = file.file.read()
    text = extract_text(file.filename or "", data).strip()
    if len(text) < 50:
        raise HTTPException(400, "Could not extract text (scanned PDF or empty file?)")
    analysis = analyze_text(text)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO resumes (user_id, filename, text, analysis) VALUES (?,?,?,?)",
        (user_id, file.filename, text, json.dumps(analysis)),
    )
    conn.commit()
    resume_id = cur.lastrowid
    conn.close()
    return {"resume_id": resume_id, "analysis": analysis}

@router.get("/{resume_id}")
def get_resume(resume_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db()
    row = conn.execute("SELECT * FROM resumes WHERE id = ? AND user_id = ?",
                       (resume_id, user_id)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Resume not found")
    return {"resume_id": row["id"], "filename": row["filename"],
            "analysis": json.loads(row["analysis"] or "{}")}