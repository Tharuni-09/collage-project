DROP TABLE IF EXISTS resumes;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    is_hod INTEGER DEFAULT 0
);

CREATE TABLE students (
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

CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL REFERENCES users(uid),
    student_id INTEGER REFERENCES users(uid),
    pdf_content BLOB,
    title TEXT DEFAULT 'Resume',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL  -- 'ACSML', 'NCSML', 'DCSML'
);

-- Insert default departments
INSERT OR IGNORE INTO departments (name) VALUES ('ACSML');
INSERT OR IGNORE INTO departments (name) VALUES ('NCSML');
INSERT OR IGNORE INTO departments (name) VALUES ('DCSML');

-- Notes table
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (faculty_id) REFERENCES users(id)
);

-- Faculty Todos table
CREATE TABLE IF NOT EXISTS faculty_todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER NOT NULL,
    subject_name TEXT NOT NULL,
    department_name TEXT NOT NULL,
    details TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty_id) REFERENCES users(uid)
);

ALTER TABLE papers ADD COLUMN image_path TEXT;
ALTER TABLE papers ADD COLUMN status TEXT DEFAULT 'pending';
ALTER TABLE papers ADD COLUMN approved_by TEXT;
ALTER TABLE papers ADD COLUMN approved_at TEXT;