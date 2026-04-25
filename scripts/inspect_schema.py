import sqlite3

conn = sqlite3.connect("podblendz.db")
rows = conn.execute("PRAGMA table_info(episodes);").fetchall()

for row in rows:
    print(row)

conn.close()