import json
from fastapi import APIRouter, Depends, HTTPException
from Backend.auth_router import get_current_user
from Backend.db_setup import get_db
from Backend.llm import call_llm_json

router = APIRouter(prefix="/recommend", tags=["recommend"])

SYSTEM_PROMPT = """You match a candidate resume against job postings.
Return ONLY JSON: {"recommendations": [{"job_id": int, "match_score": 0-100,
"explanation": "2-3 sentences why this job fits or not",
"matched_skills": ["..."], "missing_skills": ["..."]}]}
Include every job provided. Base scores strictly on the resume content."""

@router.post("/{resume_id}")
def recommend(resume_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db()
    resume = conn.execute("SELECT * FROM resumes WHERE id = ? AND user_id = ?",
                          (resume_id, user_id)).fetchone()
    jobs = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    if not resume:
        raise HTTPException(404, "Resume not found")
    if not jobs:
        raise HTTPException(400, "No jobs in the system yet")

    jobs_payload = [{"job_id": j["id"], "title": j["title"], "company": j["company"],
                     "requirements": j["requirements"], "description": j["description"][:600]}
                    for j in jobs]
    user_msg = f"Resume:\n{resume['text'][:8000]}\n\nJobs:\n{json.dumps(jobs_payload)}"
    result = call_llm_json(SYSTEM_PROMPT, user_msg)

    by_id = {j["id"]: j for j in jobs}
    out = []
    for rec in result.get("recommendations", []):
        job = by_id.get(rec.get("job_id"))
        if job:
            rec["title"] = job["title"]
            rec["company"] = job["company"]
            out.append(rec)
    out.sort(key=lambda r: r.get("match_score", 0), reverse=True)
    return {"recommendations": out}