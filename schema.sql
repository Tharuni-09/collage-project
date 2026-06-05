<<<<<<< HEAD
DROP TABLE IF EXISTS resumes;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
=======
-- FIXED SCHEMA
CREATE TABLE IF NOT EXISTS users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
>>>>>>> 8cae6f965907b79ec4473874e39a2ad25594fa48
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT
);

<<<<<<< HEAD
CREATE TABLE students (
    uid INTEGER PRIMARY KEY,
=======
CREATE TABLE IF NOT EXISTS students (
    uid INTEGER PRIMARY KEY REFERENCES users(uid),
>>>>>>> 8cae6f965907b79ec4473874e39a2ad25594fa48
    department TEXT NOT NULL,
    roll TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    cgpa REAL DEFAULT 0.0,
    sgpa REAL DEFAULT 0.0,
    attendance INTEGER DEFAULT 0,
    email TEXT,
    phone TEXT,
    address TEXT,
    date_of_birth TEXT
);

<<<<<<< HEAD
CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    uid INTEGER NOT NULL,
    pdf_content BLOB,
    title TEXT DEFAULT 'Resume',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (student_id) REFERENCES students(uid),
    FOREIGN KEY (uid) REFERENCES students(uid)
);

INSERT INTO users
(username, password_hash, name, role, email, phone)
VALUES (
    'student',
    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
    'Student One',
    'student',
    'student1@example.com',
    '9876543210'
);

INSERT INTO users
(username, password_hash, name, role, email, phone)
VALUES (
    'faculty',
    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
    'Dr. Faculty One',
    'faculty',
    'faculty@example.com',
    '9876543211'
);
INSERT INTO students
(uid, department, roll, name, cgpa, sgpa, attendance)
VALUES
(1, 'ACSML', '111704049001', 'Student One', 0.0, 0.0, 100);

-- NCSML student seed data
INSERT INTO users
(username, password_hash, name, role, email, phone)
VALUES
('111725049043', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd9e1f3c2b1c8b6100b', 'M.Manohar', 'student', 'm.manohar@example.com', '');
INSERT INTO students
(uid, department, roll, name, cgpa, sgpa, attendance)
VALUES
(111725049043, 'NCSML', '111725049043', 'M.Manohar', 8.83, 8.83, 95);

INSERT INTO users
(username, password_hash, name, role, email, phone)
VALUES
('111725049035', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd9e1f3c2b1c8b6100b', 'J.Naga Bheema Prasadu', 'student', 'j.naga@example.com', '');
INSERT INTO students
(uid, department, roll, name, cgpa, sgpa, attendance)
VALUES
(111725049035, 'NCSML', '111725049035', 'J.Naga Bheema Prasadu', 8.96, 8.96, 80);

INSERT INTO users
(username, password_hash, name, role, email, phone)
VALUES
('111725049020', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd9e1f3c2b1c8b6100b', 'A.Asmitha', 'student', 'a.asmitha@example.com', '');
INSERT INTO students
(uid, department, roll, name, cgpa, sgpa, attendance)
VALUES
(111725049020, 'NCSML', '111725049020', 'A.Asmitha', 9.22, 9.22, 78);

INSERT INTO users
(username, password_hash, name, role, email, phone)
VALUES
('111725049001', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd9e1f3c2b1c8b6100b', 'A.Sahasra', 'student', 'a.sahasra@example.com', '');
INSERT INTO students
(uid, department, roll, name, cgpa, sgpa, attendance)
VALUES
(111725049001, 'NCSML', '111725049001', 'A.Sahasra', 9.0, 9.0, 88);

INSERT INTO users
(username, password_hash, name, role, email, phone)
VALUES
('111725049010', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd9e1f3c2b1c8b6100b', 'K.Priya', 'student', 'k.priya@example.com', '');
INSERT INTO students
(uid, department, roll, name, cgpa, sgpa, attendance)
VALUES
(111725049010, 'NCSML', '111725049010', 'K.Priya', 9.6, 9.6, 92);

INSERT INTO users
(username, password_hash, name, role, email, phone)
VALUES
('111725049011', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd9e1f3c2b1c8b6100b', 'P Sri sravya', 'student', 'p.sri@example.com', '');
INSERT INTO students
(uid, department, roll, name, cgpa, sgpa, attendance)
VALUES
(111725049011, 'NCSML', '111725049011', 'P Sri sravya', 9.3, 9.3, 90);
=======
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
>>>>>>> 8cae6f965907b79ec4473874e39a2ad25594fa48
