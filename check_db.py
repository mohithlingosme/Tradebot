import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "finbot.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(table[0])
conn.close()
