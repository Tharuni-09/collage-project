CREATE TABLE users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT,
    phone TEXT
);

CREATE TABLE students (
    uid INTEGER PRIMARY KEY,
    department TEXT NOT NULL,
    roll TEXT NOT NULL,
    name TEXT NOT NULL,
    cgpa REAL DEFAULT 0.0,
    sgpa REAL DEFAULT 0.0,
    attendance INTEGER DEFAULT 0
);

CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    uid INTEGER NOT NULL,
    pdf_path TEXT NOT NULL,
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
