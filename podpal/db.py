import os
import sqlite3
from typing import Optional, List
from dataclasses import dataclass

# Resolve DB at project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "podcast_pal.db")


@dataclass
class Transcript:
    id: int
    episode_id: int
    text: str


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def ensure_tables() -> None:
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY,
            episode_id INTEGER,
            content TEXT
        )
        """
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------------
# Public API used by main.py
# ------------------------------------------------------------

def save_transcript(episode_id: int, text: str) -> None:
    ensure_tables()
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM transcripts WHERE episode_id = ?", (episode_id,))
    row = cur.fetchone()

    if row:
        cur.execute(
            "UPDATE transcripts SET content = ? WHERE episode_id = ?",
            (text, episode_id),
        )
    else:
        cur.execute(
            "INSERT INTO transcripts (episode_id, content) VALUES (?, ?)",
            (episode_id, text),
        )

    conn.commit()
    conn.close()


def get_transcript(episode_id: int) -> Optional[Transcript]:
    ensure_tables()
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, episode_id, content FROM transcripts WHERE episode_id = ?",
        (episode_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return Transcript(id=row[0], episode_id=row[1], text=row[2])


def list_transcripts() -> List[Transcript]:
    ensure_tables()
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, episode_id, content FROM transcripts ORDER BY episode_id")
    rows = cur.fetchall()
    conn.close()

    return [Transcript(id=r[0], episode_id=r[1], text=r[2]) for r in rows]


def search_transcripts(term: str) -> List[Transcript]:
    ensure_tables()
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, episode_id, content FROM transcripts WHERE content LIKE ?",
        (f"%{term}%",),
    )
    rows = cur.fetchall()
    conn.close()

    return [Transcript(id=r[0], episode_id=r[1], text=r[2]) for r in rows]


def delete_transcript(episode_id: int) -> None:
    ensure_tables()
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM transcripts WHERE episode_id = ?", (episode_id,))
    conn.commit()
    conn.close()


def backup() -> None:
    ensure_tables()
    backup_path = DB_PATH + ".backup"
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as src, open(backup_path, "wb") as dst:
            dst.write(src.read())
            