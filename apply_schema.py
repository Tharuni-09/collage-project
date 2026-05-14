import sqlite3
db = sqlite3.connect("database/ml_dept.db")
# Find resumes that don't have a matching student
orphan_resumes = db.execute("SELECT r.uid FROM resumes r LEFT JOIN students s ON r.uid = s.uid WHERE s.uid IS NULL").fetchall()
print(f"Resumes with no matching student UID: {orphan_resumes}")
db.close()