import sqlite3
import os

DB_PATH = "database/ml_dept.db"

# Ensure folder exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

db = sqlite3.connect(DB_PATH)

with open("schema.sql", "r", encoding="utf-8") as f:
    sql_content = f.read()
    db.executescript(sql_content)

db.commit()
db.close()
print("✅ Created fresh database from schema.sql")