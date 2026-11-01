import sqlite3
from pathlib import Path

# Find project root
project_root = Path(__file__).resolve().parents[3]

db_path = project_root / "podblendz.db"

print(f"Using database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table';
""")

tables = cursor.fetchall()

print("\nDATABASE TABLES\n")

for table in tables:
    print(table[0])

conn.close()