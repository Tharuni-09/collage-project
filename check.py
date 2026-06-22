import sqlite3

# Connect to your database
db = sqlite3.connect("database/ml_dept.db")
cursor = db.cursor()

# Get column names for students and resumes tables
for table in ["students", "resumes"]:
    print(f"--- Columns in {table} ---")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"Column Name: {col[1]}")

db.close()