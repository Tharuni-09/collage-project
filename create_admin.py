import sqlite3
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "database", "ml_dept.db")

def create_admin():
    username = input("Enter admin username (e.g. admin_01): ").strip()
    password = input("Enter admin password: ").strip()
    name = input("Enter admin full name: ").strip()
    
    if not username or not password or not name:
        print("Error: All fields are required.")
        return

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, name) VALUES (?, ?, ?, ?)",
            (username, password_hash, 'admin', name)
        )
        conn.commit()
        print(f"Success! Admin account '{username}' has been created.")
    except sqlite3.IntegrityError:
        print("Error: Username already exists.")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin()
