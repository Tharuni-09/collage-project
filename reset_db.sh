#!/bin/bash

python - <<'PY'
import sqlite3

conn = sqlite3.connect("your_database.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS resumes")
cur.execute("DROP TABLE IF EXISTS students")
cur.execute("DROP TABLE IF EXISTS users")

conn.commit()
conn.close()

print("Database tables dropped successfully")
PY