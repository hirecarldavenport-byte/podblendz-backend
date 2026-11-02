import sqlite3

conn = sqlite3.connect("podblendz.db")
cur = conn.cursor()

cur.execute("""
SELECT id, title, board
FROM blends
WHERE board = 'Uncategorized'
ORDER BY created_at DESC
""")

rows = cur.fetchall()

print("\n=== UNCATEGORIZED BLENDZ ===\n")

for row in rows:
    print(f"ID: {row[0]}")
    print(f"TITLE: {row[1]}")
    print(f"BOARD: {row[2]}")
    print("-" * 80)

print(f"\nTotal Uncategorized: {len(rows)}")

conn.close()