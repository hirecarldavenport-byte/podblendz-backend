import sqlite3

conn = sqlite3.connect("podblendz.db")
cur = conn.cursor()

# Career blend
cur.execute("""
UPDATE blends
SET board='Business'
WHERE id='2c37437f-e13d-421f-a952-b14786830cb2'
""")

# Education blends
cur.execute("""
UPDATE blends
SET board='Education'
WHERE title LIKE '%children graduating in 2040%'
""")

conn.commit()

print("✅ Boards updated")

conn.close()
