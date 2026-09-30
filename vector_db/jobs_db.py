# jobs_db.py
from vector_store import get_conn

def init_jobs_table():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()