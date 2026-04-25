import sqlite3
import json
from pathlib import Path

# =====================================================
# CONFIG
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "podblendz.db"
SQL_PATH = BASE_DIR / "sql" / "select_education_learning_candidates.sql"
OUTPUT_PATH = BASE_DIR / "data" / "selected_episodes" / "education_learning.json"

# =====================================================
# MAIN
# =====================================================

def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    with open(SQL_PATH, "r", encoding="utf-8") as f:
        query = f.read()

    rows = conn.execute(query).fetchall()
    episodes = [dict(row) for row in rows]

    print(f"✅ Selected {len(episodes)} episodes")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2)

    conn.close()


if __name__ == "__main__":
    main()