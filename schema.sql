-- FIXED SCHEMA
CREATE TABLE IF NOT EXISTS users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS students (
    uid INTEGER PRIMARY KEY REFERENCES users(uid),
    department TEXT NOT NULL,
    roll TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    cgpa REAL DEFAULT 0.0,
    sgpa REAL DEFAULT 0.0,
    attendance INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL REFERENCES users(uid),
    pdf_path TEXT NOT NULL,
    title TEXT DEFAULT 'Resume',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- SAMPLE DATA (password: 123456)
INSERT OR IGNORE INTO users (uid, username, password_hash, name, role) VALUES
(1, 'student_acsml', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'ACSML Student', 'student'),
(2, 'student_ncsml', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'NCSML Student', 'student'),
(3, 'student_dcsml', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'DCSML Student', 'student'),
(101, 'faculty1', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'Dr. Faculty', 'faculty');

INSERT OR IGNORE INTO students (uid, department, roll, name, cgpa, attendance) VALUES
(1, 'ACSML', 'ACS001', 'ACSML Student', 8.5, 95),
(2, 'NCSML', 'NCS001', 'NCSML Student', 8.2, 88),
(3, 'DCSML', 'DCS001', 'DCSML Student', 9.0, 92);

-- Fake resume paths (app creates real ones later)
INSERT OR IGNORE INTO resumes (uid, pdf_path, title) VALUES
(1, 'resumes/fake_acsml.pdf', 'ACSML Resume'),
(2, 'resumes/fake_ncsml.pdf', 'NCSML Resume'),
(3, 'resumes/fake_dcsml.pdf', 'DCSML Resume');
