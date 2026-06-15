import sqlite3, hashlib, json

db = 'database/ml_dept.db'
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()

uids = [101]
usernames = ['faculty_1']
results = {}
for u in uids:
    row = cur.execute('SELECT uid, username, role, email, password_hash FROM users WHERE uid=?', (u,)).fetchone()
    results[f'uid_{u}'] = dict(row) if row else None
for name in usernames:
    row = cur.execute('SELECT uid, username, role, email, password_hash FROM users WHERE username=?', (name,)).fetchone()
    results[f'user_{name}'] = dict(row) if row else None

print(json.dumps(results, indent=2))
con.close()