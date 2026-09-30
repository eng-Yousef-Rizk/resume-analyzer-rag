from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Backend.db_setup import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobIn(BaseModel):
    title: str
    company: str
    description: str
    requirements: str

@router.post("", status_code=201)
def create_job(job: JobIn):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO jobs (title, company, description, requirements) VALUES (?,?,?,?)",
        (job.title, job.company, job.description, job.requirements),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **job.model_dump()}

# FR-7: GET /jobs?q=python  -> search, GET /jobs -> list all
@router.get("")
def list_jobs(q: Optional[str] = None):
    sql = "SELECT * FROM jobs"
    params = []
    if q:
        sql += " WHERE title LIKE ? OR company LIKE ? OR description LIKE ? OR requirements LIKE ?"
        params = [f"%{q}%"] * 4
    sql += " ORDER BY id DESC"
    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/{job_id}")
def get_job(job_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Job not found")
    return dict(row)

@router.put("/{job_id}")
def update_job(job_id: int, job: JobIn):
    conn = get_db()
    cur = conn.execute(
        "UPDATE jobs SET title=?, company=?, description=?, requirements=? WHERE id=?",
        (job.title, job.company, job.description, job.requirements, job_id),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "Job not found")
    return {"id": job_id, **job.model_dump()}

@router.delete("/{job_id}")
def delete_job(job_id: int):
    conn = get_db()
    cur = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "Job not found")
    return {"deleted": job_id}