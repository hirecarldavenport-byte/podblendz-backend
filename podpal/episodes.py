import sqlite3
from typing import Dict, List

def get_latest_episodes_by_podcaster(
    conn: sqlite3.Connection,
    podcaster_ids: List[int],
    limit_per_podcaster: int = 20,
) -> Dict[int, list]:
    """
    Fetch latest episodes per podcaster.
    """

    episodes_by_podcaster = {}

    for podcaster_id in podcaster_ids:
        rows = conn.execute(
            """
            SELECT *
            FROM episodes
            WHERE podcaster_id = ?
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (podcaster_id, limit_per_podcaster),
        ).fetchall()

        episodes_by_podcaster[podcaster_id] = rows

    return episodes_by_podcaster
