-- ========================
-- Core tables (safe re-creation)
-- ========================

CREATE TABLE IF NOT EXISTS users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    is_hod INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS students (
    uid INTEGER PRIMARY KEY REFERENCES users(uid),
    department TEXT NOT NULL,
    roll TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    cgpa REAL DEFAULT 0.0,
    sgpa REAL DEFAULT 0.0,
    attendance INTEGER DEFAULT 0,
    address TEXT,
    date_of_birth TEXT
);

CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL REFERENCES users(uid),
    student_id INTEGER REFERENCES users(uid),
    pdf_content BLOB,
    pdf_path TEXT,
    title TEXT DEFAULT 'Resume',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ========================
-- Departments & Notes
-- ========================

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT OR IGNORE INTO departments (name) VALUES ('ACSML');
INSERT OR IGNORE INTO departments (name) VALUES ('NCSML');
INSERT OR IGNORE INTO departments (name) VALUES ('DCSML');

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_content BLOB,
    mime_type TEXT DEFAULT 'application/octet-stream',
    department_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- ========================
-- Faculty Todos & Timetable
-- ========================

CREATE TABLE IF NOT EXISTS faculty_todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER NOT NULL,
    subject_name TEXT NOT NULL,
    department_name TEXT NOT NULL,
    task_date TEXT,
    period TEXT,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty_id) REFERENCES users(uid)
);

CREATE TABLE IF NOT EXISTS faculty_timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    period_number INTEGER NOT NULL,
    subject_name TEXT NOT NULL,
    department_name TEXT NOT NULL,
    FOREIGN KEY (faculty_id) REFERENCES users(uid),
    UNIQUE(faculty_id, day_of_week, period_number)
);

-- ========================
-- Previous Year Papers
-- ========================

CREATE TABLE IF NOT EXISTS previous_year_papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    branch TEXT DEFAULT 'N/A',
    department TEXT,
    year INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    no_of_pages INTEGER DEFAULT 0,
    photo_limit INTEGER DEFAULT 1,
    approved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS paper_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES previous_year_papers(id)
);

-- ========================
-- Outreach & Gallery
-- ========================

CREATE TABLE IF NOT EXISTS outreach_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    year TEXT NOT NULL,
    date TEXT,
    department TEXT,
    venue TEXT NOT NULL,
    participants TEXT NOT NULL,
    description TEXT,
    photo TEXT,
    approved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS gallery_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    department TEXT,
    date TEXT,
    photo TEXT NOT NULL,
    approved INTEGER DEFAULT 0,
    faculty_id INTEGER
);

-- ========================
-- Admin Settings
-- ========================

CREATE TABLE IF NOT EXISTS admin_settings (
    id INTEGER PRIMARY KEY,
    resume_builder INTEGER DEFAULT 1,
    student_signup INTEGER DEFAULT 1,
    faculty_upload INTEGER DEFAULT 1,
    ai_resume_builder INTEGER DEFAULT 1
);

INSERT OR IGNORE INTO admin_settings (id) VALUES (1);