import hashlib, hmac, os, secrets
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from Backend.db_setup import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

class Creds(BaseModel):
    email: str
    password: str

def hash_password(pw: str, salt: Optional[bytes] = None) -> str:
    salt = salt or os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000)
    return salt.hex() + ":" + h.hex()

def verify_password(pw: str, stored: str) -> bool:
    salt_hex, _ = stored.split(":")
    return hmac.compare_digest(hash_password(pw, bytes.fromhex(salt_hex)), stored)

def get_current_user(authorization: Optional[str] = Header(None)) -> int:
    """Use as: user_id: int = Depends(get_current_user). Header: Authorization: Bearer <token>"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization[7:]
    conn = get_db()
    row = conn.execute("SELECT user_id FROM sessions WHERE token = ?", (token,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(401, "Invalid token")
    return row["user_id"]

@router.post("/register", status_code=201)
def register(c: Creds):
    if len(c.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)",
                     (c.email.lower().strip(), hash_password(c.password)))
        conn.commit()
    except Exception:
        raise HTTPException(400, "Email already registered")
    finally:
        conn.close()
    return {"message": "registered"}

@router.post("/login")
def login(c: Creds):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (c.email.lower().strip(),)).fetchone()
    if not user or not verify_password(c.password, user["password_hash"]):
        conn.close()
        raise HTTPException(401, "Wrong email or password")
    token = secrets.token_hex(32)
    conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user["id"]))
    conn.commit()
    conn.close()
    return {"token": token}

@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        conn = get_db()
        conn.execute("DELETE FROM sessions WHERE token = ?", (authorization[7:],))
        conn.commit()
        conn.close()
    return {"message": "logged out"}