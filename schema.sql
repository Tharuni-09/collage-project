-- ========================
-- TABLE: users
-- ========================
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER UNIQUE NOT NULL,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT,
    phone TEXT
);

-- ========================
-- TABLE: students
-- ========================
CREATE TABLE students (
    uid INTEGER PRIMARY KEY ,
    department TEXT NOT NULL,
    roll TEXT NOT NULL,
    name TEXT NOT NULL,
    cgpa REAL DEFAULT 0.0,
    sgpa REAL DEFAULT 0.0,
    attendance INTEGER DEFAULT 0
);

-- ========================
-- TABLE: resumes
-- ========================
CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    uid INTEGER NOT NULL,
    pdf_path TEXT NOT NULL,
    title TEXT DEFAULT 'Resume',
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (student_id) REFERENCES students (id),
    FOREIGN KEY (uid) REFERENCES students (uid)
);

SELECT uid, pdf_path FROM resumes LIMIT 1;

-- ========================
-- INSERT SAMPLE DATA (with SHA‑256 hash of "123456")
-- ========================
INSERT INTO users
(uid, username, password_hash, name, role, email, phone)
VALUES
(
    1,
    'student_1',
    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',  -- sha256("123456")
    'Student One',
    'student',
    'student1@example.com',
    '9876543210'
);

INSERT INTO students
(uid, department, roll, name, cgpa, sgpa, attendance)
VALUES
(
    1,
    'ACSML',
    '111726049001',
    'Student One',
    8.5,
    9.0,
    90
);

INSERT INTO users
(uid, username, password_hash, name, role, email, phone)
VALUES
(
    101,
    'faculty_1',
    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',  -- sha256("123456")
    'Dr. Faculty One',
    'faculty',
    'faculty1@example.com',
    '9876543211'
);