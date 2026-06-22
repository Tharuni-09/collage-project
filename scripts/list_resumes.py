import sqlite3, json
con=sqlite3.connect('database/ml_dept.db')
con.row_factory=sqlite3.Row
cur=con.cursor()
count = cur.execute('SELECT COUNT(*) c FROM resumes').fetchone()['c']
print('RESUMES_COUNT:', count)
rows=cur.execute('SELECT r.id, r.uid, r.title, r.created_at, s.roll, s.name, s.department FROM resumes r JOIN students s ON r.uid = s.uid ORDER BY s.department, s.roll LIMIT 20').fetchall()
print('SAMPLE:', len(rows))
for row in rows:
    print(dict(row))
con.close()