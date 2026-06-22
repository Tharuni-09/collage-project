import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "ml_dept.db")
db = sqlite3.connect(DB_PATH)

try:
    cursor = db.execute("PRAGMA table_info(resumes)")
    cols = [row[1] for row in cursor.fetchall()]
    
    if "pdf_path" in cols:
        print("Legacy 'pdf_path' found. Reconstructing table...")
        db.executescript("""
            CREATE TABLE resumes_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                uid INTEGER NOT NULL,
                pdf_content BLOB,
                title TEXT DEFAULT 'Resume',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (student_id) REFERENCES students(uid),
                FOREIGN KEY (uid) REFERENCES students(uid)
            );
            INSERT INTO resumes_new (id, student_id, uid, title, created_at)
            SELECT id, student_id, uid, title, created_at FROM resumes;
            DROP TABLE resumes;
            ALTER TABLE resumes_new RENAME TO resumes;
        """)
        print("✅ Migration successful: legacy column removed.")
    elif "pdf_content" not in cols:
        db.execute("ALTER TABLE resumes ADD COLUMN pdf_content BLOB")
        print("✅ Migration successful: 'pdf_content' added.")
except Exception as e:
    print(f"❌ Migration failed: {e}")
db.close()