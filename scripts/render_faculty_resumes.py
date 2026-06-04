import sqlite3
from jinja2 import Environment, FileSystemLoader
import os

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env = Environment(loader=FileSystemLoader(os.path.join(root, 'templates')))
# Provide a stub for url_for used in templates
env.globals['url_for'] = lambda endpoint, **kwargs: f'/{endpoint.replace(".", "/")}'
tmpl = env.get_template('faculty-resumes.html')
con = sqlite3.connect(os.path.join(root, 'database', 'ml_dept.db'))
con.row_factory = sqlite3.Row
rows = con.execute('SELECT r.id, r.uid, r.title, r.pdf_path, r.created_at, s.roll, s.name, s.department FROM resumes r JOIN students s ON r.uid = s.uid ORDER BY s.department, s.roll').fetchall()
resumes = [dict(r) for r in rows]
out = tmpl.render(resumes=resumes, session={'role': 'faculty'})
print('RENDER LEN', len(out))
print(out[:2000])
con.close()