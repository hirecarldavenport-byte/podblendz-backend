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

for row in rows:
    print(row)

conn.close()