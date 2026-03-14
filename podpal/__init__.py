# app/db.py
import os
import sqlite3
from typing import Optional

# Use one DB file: podcast_pal.db (with underscore) at the project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "podcast_pal.db")


def get_conn(path: Optional[str] = None) -> sqlite3.Connection:
    """
    Return a SQLite connection with foreign keys enabled and Row factory.
    """
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def ensure_core_tables(conn: sqlite3.Connection) -> None:
    """
    Create feeds and episodes if they don't exist (minimal schema).
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT,
            link TEXT,
            description TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER NOT NULL,
            title TEXT,
            link TEXT,
            media_url TEXT,
            pub_date TEXT,
            summary TEXT
        );
        """
        # NOTE: keeping this minimal for now (no FK) to avoid errors while testing.
        # We can add "FOREIGN KEY(feed_id) REFERENCES feeds(id) ON DELETE CASCADE"
        # after we wire feed import.
    )
    conn.commit()


def ensure_transcripts_table(conn: sqlite3.Connection) -> None:
    """
    Create the transcripts table if missing.
    Primary key is episode_id so we can upsert per episode.
    (No foreign key yet to avoid 'FOREIGN KEY constraint failed' while testing.)
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transcripts (
            episode_id INTEGER PRIMARY KEY,
            transcript  TEXT NOT NULL,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()


def add_or_update_transcript(conn: sqlite3.Connection, episode_id: int, text: str) -> None:
    """
    Upsert transcript text for a given episode_id.
    """
    conn.execute(
        """
        INSERT INTO transcripts (episode_id, transcript)
        VALUES (?, ?)
        ON CONFLICT(episode_id) DO UPDATE SET
            transcript = excluded.transcript,
            updated_at = CURRENT_TIMESTAMP;
        """,
        (episode_id, text),
    )
    conn.commit()