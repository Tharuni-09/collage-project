from flask import (
    Flask, flash, send_file, render_template, request,
    redirect, session, jsonify, url_for, make_response
)
import sqlite3
import hashlib
import os
import io
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle, HRFlowable
from reportlab.lib import colors
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# APP SETUP
# ---------------------------------------------------------------------------
app = Flask(__name__,
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)
app.secret_key = os.environ.get("SECRET_KEY", "ml_dept_secret_2026")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
app.config['SESSION_COOKIE_PERMANENT']   = True
app.config['SESSION_COOKIE_SECURE']      = False
app.config['SESSION_COOKIE_HTTPONLY']    = True
app.config['SESSION_COOKIE_SAMESITE']   = 'Lax'
app.config['MAX_CONTENT_LENGTH']        = 50 * 1024 * 1024  # 50 MB

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "database", "ml_dept.db")

NOTES_FOLDER = os.path.join(BASE_DIR, "static", "notes")
os.makedirs(NOTES_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'}

# ---------------------------------------------------------------------------
# DATABASE HELPERS
# ---------------------------------------------------------------------------
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# AUTO-INIT DATABASE
# ---------------------------------------------------------------------------
def init_database():
    db = get_db()
    try:
        # Base schema if users table doesn't exist
        users_exist = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if not users_exist:
            schema_path = os.path.join(BASE_DIR, "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, "r") as f:
                    db.executescript(f.read())

        # Always ensure these tables exist
        db.executescript("""
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
                attendance INTEGER DEFAULT 0
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

            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                mime_type TEXT DEFAULT 'application/octet-stream',
                department_id INTEGER NOT NULL,
                faculty_id INTEGER NOT NULL,
                faculty_name TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS faculty_todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_id INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                department_name TEXT NOT NULL,
                task_date TEXT NOT NULL,
                period TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS faculty_timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_id INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                period_number INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                department_name TEXT NOT NULL,
                UNIQUE(faculty_id, day_of_week, period_number)
            );

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
                image_path TEXT NOT NULL
            );

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

            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_id INTEGER NOT NULL,
                faculty_name TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                target_dept TEXT NOT NULL DEFAULT 'ALL',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Safe column migrations for older DB files
        migrations = [
            "ALTER TABLE notes ADD COLUMN faculty_name TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE notes ADD COLUMN mime_type TEXT DEFAULT 'application/octet-stream'",
            "ALTER TABLE faculty_todos ADD COLUMN period TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE previous_year_papers ADD COLUMN branch TEXT DEFAULT 'N/A'",
            "ALTER TABLE previous_year_papers ADD COLUMN no_of_pages INTEGER DEFAULT 0",
            "ALTER TABLE previous_year_papers ADD COLUMN photo_limit INTEGER DEFAULT 1",
            "ALTER TABLE previous_year_papers ADD COLUMN approved INTEGER DEFAULT 0",
            "ALTER TABLE outreach_programs ADD COLUMN approved INTEGER DEFAULT 0",
        ]
        for m in migrations:
            try:
                db.execute(m)
            except Exception:
                pass

        # Seed departments
        for dept in ["ACSML", "NCSML", "DCSML"]:
            try:
                db.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (dept,))
            except Exception:
                pass

        db.commit()
    finally:
        db.close()


with app.app_context():
    init_database()


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def should_print_section(text, user_response):
    if not text or not text.strip():
        return False
    low = user_response.strip().lower()
    return low not in ["no", "false", "0", "none", "not applicable", "na"]


def elaborate(text, section_name):
    if not text or section_name not in ["skills", "projects", "internships"]:
        return text
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return ""
    if section_name == "skills":
        bullets = []
        for line in lines:
            if not line:
                continue
            if line.lower().startswith("python"):
                bullets.append("Python: Proficient in core Python, OOP, and popular libraries such as NumPy and Pandas.")
            elif line.lower().startswith("flask"):
                bullets.append("Flask: Developed web applications and REST APIs using Flask and SQLite.")
            elif "machine learning" in line.lower() or line.lower().startswith("ml"):
                bullets.append("Machine Learning: Experience with classification, regression, and neural networks.")
            elif "sql" in line.lower() or "database" in line.lower():
                bullets.append("SQL & Databases: Designed and queried SQLite and MySQL databases.")
            elif "html" in line.lower() and "css" in line.lower():
                bullets.append("Web Technologies: Built responsive websites using HTML, CSS, and JavaScript.")
            else:
                bullets.append(f"{line}: Comfortable applying this technology to real-world projects.")
        return "\n".join(bullets)
    if section_name == "projects":
        bullets = []
        for i, line in enumerate(lines):
            if i == 0 and len(lines) == 1:
                bullets.append(f"{line} – A well-structured project applying core technology stack concepts.")
            elif i == 0:
                bullets.append(f"Project: {line}")
            else:
                bullets.append(f"• {line}")
        return "\n".join(bullets)
    if section_name == "internships":
        return "\n".join([
            "Internship role focused on practical software development in a team environment."
            if ("intern" in l.lower()) else f"• {l}"
            for l in lines
        ])
    return text


def polish_objective(obj):
    if not obj or not obj.strip():
        return ""
    obj = " ".join(obj.strip().split())
    if not obj.endswith("."):
        obj += "."
    return f"Motivated and detail-oriented professional with strong {obj[0].lower() + obj[1:]}"


# ---------------------------------------------------------------------------
# PUBLIC ROUTES
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/outreach")
def outreach():
    db = get_db()
    programs = db.execute(
        "SELECT * FROM outreach_programs WHERE approved = 1 ORDER BY id DESC"
    ).fetchall()
    db.close()
    return render_template("outreach.html", programs=programs)


@app.route("/gallery")
def gallery():
    db = get_db()
    events = db.execute(
        "SELECT * FROM gallery_events WHERE approved = 1 ORDER BY id DESC"
    ).fetchall()
    db.close()
    return render_template("gallery.html", events=events)


@app.route("/add_outreach_program", methods=["POST"])
def add_outreach_program():
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    title        = request.form.get("title", "")
    year         = request.form.get("year", "")
    date         = request.form.get("date", "")
    department   = request.form.get("department", "")
    venue        = request.form.get("venue", "")
    participants = request.form.get("participants", "")
    description  = request.form.get("description", "")
    photo_file   = request.files.get("photo")
    photo_name   = ""
    if photo_file and photo_file.filename:
        photo_name = secure_filename(photo_file.filename)
        photo_path = os.path.join(BASE_DIR, "static", "outreach", photo_name)
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        photo_file.save(photo_path)
    db = get_db()
    db.execute(
        "INSERT INTO outreach_programs (title,year,date,department,venue,participants,description,photo,approved) VALUES (?,?,?,?,?,?,?,?,0)",
        (title, year, date, department, venue, participants, description, photo_name)
    )
    db.commit()
    db.close()
    flash("Outreach program submitted for approval.", "success")
    return redirect(url_for("outreach"))


@app.route("/add_gallery_event", methods=["POST"])
def add_gallery_event():
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    title       = request.form.get("title", "")
    description = request.form.get("description", "")
    department  = request.form.get("department", "")
    date        = request.form.get("date", "")
    photo_file  = request.files.get("photo")
    photo_name  = "placeholder.jpg"
    if photo_file and photo_file.filename:
        photo_name = secure_filename(photo_file.filename)
        photo_path = os.path.join(BASE_DIR, "static", "images", photo_name)
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        photo_file.save(photo_path)
    db = get_db()
    db.execute(
        "INSERT INTO gallery_events (title,description,department,date,photo,approved,faculty_id) VALUES (?,?,?,?,?,0,?)",
        (title, description, department, date, photo_name, session.get("uid"))
    )
    db.commit()
    db.close()
    flash("Gallery event submitted for approval.", "success")
    return redirect(url_for("gallery"))


# ---------------------------------------------------------------------------
# AUTH ROUTES
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        message = request.args.get("message", "")
        return render_template("login.html", error=None, message=message)

    uid      = request.form.get("uid", "").strip()
    password = request.form.get("password", "").strip()
    role     = request.form.get("role", "").strip().lower()

    if not all([uid, password, role]):
        return render_template("login.html", error="All fields are required.", message="")

    try:
        uid_int = int(uid)
    except ValueError:
        return render_template("login.html", error="UID must be a number.", message="")

    h  = hashlib.sha256(password.encode()).hexdigest()
    db = get_db()
    row = db.execute(
        "SELECT uid, username, password_hash, role, name FROM users WHERE uid = ?",
        [uid_int]
    ).fetchone()
    db.close()

    if not row:
        return render_template("login.html", error="UID not found.", message="")
    if row["password_hash"] != h:
        return render_template("login.html", error="Incorrect password.", message="")
    if row["role"] != role:
        return render_template("login.html", error=f"This UID is registered as '{row['role']}', not '{role}'.", message="")

    session.permanent = True
    session["uid"]      = row["uid"]
    session["username"] = row["username"]
    session["role"]     = row["role"]
    session["name"]     = row["name"]

    if row["role"] == "student":
        return redirect(url_for("student_dashboard"))
    elif row["role"] == "admin":
        return redirect("/admin-dashboard")
    else:
        return redirect(url_for("faculty_dashboard"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", error=None, message=None)

    name     = request.form.get("name", "").strip()
    uid_str  = request.form.get("uid", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    role     = request.form.get("role", "student").strip().lower()

    if not all([name, uid_str, email, password]):
        return render_template("signup.html", error="All fields are required.", message=None)

    try:
        uid = int(uid_str)
    except ValueError:
        return render_template("signup.html", error="UID must be a number.", message=None)

    h  = hashlib.sha256(password.encode()).hexdigest()
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (uid, username, password_hash, role, name, email) VALUES (?,?,?,?,?,?)",
            (uid, f"user_{uid}", h, role, name, email)
        )
        db.commit()
        db.close()
        return render_template("signup.html", error=None, message="Account created! You can now login.")
    except sqlite3.IntegrityError:
        db.close()
        return render_template("signup.html", error="UID already exists. Please use a different UID.", message=None)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forget_password.html", error=None, message=None)
    identifier = request.form.get("identifier", "").strip()
    if not identifier:
        return render_template("forget_password.html", error="Please enter your UID, email or phone.", message=None)
    return render_template("forget_password.html", error=None,
                           message=f"If '{identifier}' is registered, your password reset info has been sent.")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# STUDENT ROUTES
# ---------------------------------------------------------------------------

@app.route("/student-dashboard")
def student_dashboard():
    uid = session.get("uid")
    if not uid or session.get("role") != "student":
        return redirect(url_for("login"))

    db = get_db()

    student = db.execute(
        "SELECT roll, name, department, cgpa, sgpa, attendance FROM students WHERE uid = ?",
        [uid]
    ).fetchone()

    if not student:
        db.close()
        return f"<h3>Student profile not found for UID {uid}. Please contact admin.</h3>", 404

    resumes = db.execute(
        "SELECT id, uid, title, pdf_path, created_at FROM resumes WHERE uid = ? ORDER BY created_at DESC",
        [uid]
    ).fetchall()

    # Announcements relevant to this student's dept
    dept = student["department"]
    announcements = db.execute(
        """SELECT a.title, a.message, a.faculty_name, a.target_dept, a.created_at
           FROM announcements a
           WHERE a.target_dept = 'ALL' OR a.target_dept = ?
           ORDER BY a.created_at DESC LIMIT 10""",
        [dept]
    ).fetchall()

    db.close()

    return render_template(
        "student_dashboard.html",
        roll=student["roll"],
        name=student["name"],
        department=dept,
        cgpa=student["cgpa"],
        sgpa=student["sgpa"],
        attendance=student["attendance"],
        resumes=resumes,
        announcements=announcements,
    )


@app.route("/resume-form", methods=["GET", "POST"])
@app.route("/resume_form", methods=["GET", "POST"])
def resume_form():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("login"))

    db = get_db()
    user = db.execute("SELECT name, email, phone FROM users WHERE uid = ?", [uid]).fetchone()
    if not user:
        db.close()
        return "User not found", 404

    name, email, phone = user["name"], user["email"] or "", user["phone"] or ""

    fields = {k: "" for k in [
        "name_form","phone_form","email_form","linkedin","portfolio","location",
        "objective","education","technical_skills","soft_skills","work_experience",
        "internships","projects","certifications","achievements","extracurriculars",
        "languages","hobbies","references","include_references","additional_details"
    ]}

    if request.method == "POST":
        for key in fields:
            form_key = key.replace("_form", "") if key.endswith("_form") else key
            # Map name_form → name, etc.
            actual_key = {
                "name_form": "name", "phone_form": "phone", "email_form": "email"
            }.get(key, key)
            fields[key] = request.form.get(actual_key, "").strip()

        student = db.execute("SELECT uid FROM students WHERE uid = ?", [uid]).fetchone()
        if not student:
            db.close()
            return "Student profile not found. Please contact admin.", 404

        pdf_folder = os.path.join("static", "resumes")
        os.makedirs(pdf_folder, exist_ok=True)
        pdf_name = f"resume_{uid}_{int(datetime.now().timestamp())}.pdf"
        pdf_path = os.path.join(pdf_folder, pdf_name)

        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        styleSection = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=12,
                                      spaceBefore=10, spaceAfter=6)
        story = []

        name_p = Paragraph(fields["name_form"] or name, styles["Title"])
        contact_str = f"{fields['email_form'] or email} | {fields['phone_form'] or phone}"
        if fields["linkedin"]:
            contact_str += f" | LinkedIn: {fields['linkedin']}"
        story.append(name_p)
        story.append(Paragraph(contact_str, styles["BodyText"]))
        story.append(HRFlowable(color=colors.black, thickness=0.5))
        story.append(Spacer(1, 8))

        def add_section(label, text):
            if text and text.strip():
                story.append(Paragraph(label, styleSection))
                story.append(Paragraph(text.replace("\n", "<br/>"), styles["Normal"]))
                story.append(HRFlowable(color=colors.grey, thickness=0.25))
                story.append(Spacer(1, 8))

        obj = polish_objective(fields["objective"])
        if obj:
            add_section("CAREER OBJECTIVE", obj)
        add_section("EDUCATION", fields["education"])
        add_section("TECHNICAL SKILLS", elaborate(fields["technical_skills"], "skills"))
        add_section("SOFT SKILLS", fields["soft_skills"])
        add_section("WORK EXPERIENCE", fields["work_experience"])
        add_section("INTERNSHIP EXPERIENCE", elaborate(fields["internships"], "internships"))
        add_section("PROJECTS", elaborate(fields["projects"], "projects"))
        add_section("CERTIFICATIONS", fields["certifications"])
        add_section("ACHIEVEMENTS", fields["achievements"])
        add_section("EXTRACURRICULAR ACTIVITIES", fields["extracurriculars"])
        add_section("LANGUAGES", fields["languages"])
        add_section("HOBBIES / INTERESTS", fields["hobbies"])
        if should_print_section(fields["references"], fields["include_references"]):
            add_section("REFERENCES", fields["references"])
        add_section("ADDITIONAL DETAILS", fields["additional_details"])

        doc.build(story)

        rel_path = f"resumes/{pdf_name}"
        db.execute(
            "INSERT INTO resumes (uid, student_id, pdf_path, title, created_at) VALUES (?,?,?,?,?)",
            [uid, uid, rel_path, "Resume", datetime.now()]
        )
        db.commit()
        db.close()
        flash("Resume generated successfully!", "success")
        return redirect(url_for("student_dashboard"))

    db.close()
    return render_template("resume_form.html",
                           name=name, email=email, phone=phone, **{k: "" for k in [
                               "linkedin","portfolio","location","objective","education",
                               "technical_skills","soft_skills","work_experience","internships",
                               "projects","certifications","achievements","extracurriculars",
                               "languages","hobbies","references","additional_details"
                           ]})


@app.route("/view_resume/<int:resume_id>")
def view_resume(resume_id):
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("login"))
    db = get_db()
    row = db.execute("SELECT pdf_path FROM resumes WHERE id = ? AND uid = ?", [resume_id, uid]).fetchone()
    db.close()
    if not row or not row["pdf_path"]:
        return "Resume not found", 404
    full_path = os.path.join(BASE_DIR, "static", row["pdf_path"])
    if not os.path.exists(full_path):
        return "PDF file missing on disk", 404
    return send_file(full_path, mimetype="application/pdf")


@app.route("/download-resume/<int:resume_id>")
@app.route("/download_resume/<int:resume_id>")
def download_resume(resume_id):
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("login"))
    db = get_db()
    row = db.execute("SELECT pdf_path FROM resumes WHERE id = ? AND uid = ?", [resume_id, uid]).fetchone()
    db.close()
    if not row or not row["pdf_path"]:
        return "Resume not found", 404
    full_path = os.path.join(BASE_DIR, "static", row["pdf_path"])
    if not os.path.exists(full_path):
        return "PDF file not found on disk", 404
    return send_file(full_path, mimetype="application/pdf", as_attachment=True,
                     download_name=f"resume_{uid}.pdf")


@app.route("/combined_resume/<int:uid>")
def combined_resume(uid):
    if not session.get("uid"):
        return redirect(url_for("login"))
    db = get_db()
    rows = db.execute(
        "SELECT pdf_path FROM resumes WHERE uid = ? AND pdf_path IS NOT NULL ORDER BY created_at DESC",
        [uid]
    ).fetchall()
    db.close()

    if not rows:
        return "No resumes found.", 404

    # Return first available PDF as a simple stub
    for row in rows:
        full_path = os.path.join(BASE_DIR, "static", row["pdf_path"])
        if os.path.exists(full_path):
            return send_file(full_path, mimetype="application/pdf",
                             download_name=f"combined_resume_{uid}.pdf")
    return "Resume files not found on disk.", 404


@app.route("/delete-resume", methods=["POST"])
@app.route("/delete_resume", methods=["POST"])
def delete_resume():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("login"))
    resume_id = request.form.get("resume_id")
    if not resume_id:
        return "Invalid request", 400
    try:
        resume_id = int(resume_id)
    except ValueError:
        return "Invalid ID", 400
    db = get_db()
    row = db.execute("SELECT pdf_path FROM resumes WHERE id = ? AND uid = ?", [resume_id, uid]).fetchone()
    if not row:
        db.close()
        return "Not found", 404
    if row["pdf_path"]:
        full = os.path.join(BASE_DIR, "static", row["pdf_path"])
        if os.path.exists(full):
            os.remove(full)
    db.execute("DELETE FROM resumes WHERE id = ? AND uid = ?", [resume_id, uid])
    db.commit()
    db.close()
    flash("Resume deleted.", "info")
    return redirect(url_for("student_dashboard"))


# ---------------------------------------------------------------------------
# FACULTY ROUTES
# ---------------------------------------------------------------------------

@app.route("/faculty-dashboard")
@app.route("/faculty_dashboard")
def faculty_dashboard():
    uid = session.get("uid")
    if not uid or session.get("role") != "faculty":
        return redirect(url_for("login"))

    db = get_db()

    students = db.execute(
        """SELECT s.roll, s.name, s.department, s.cgpa, s.attendance, u.username, u.uid
           FROM students s JOIN users u ON s.uid = u.uid
           ORDER BY s.department, s.roll"""
    ).fetchall()

    todos = db.execute(
        "SELECT * FROM faculty_todos WHERE faculty_id = ? ORDER BY task_date, period",
        [uid]
    ).fetchall()

    timetable_list = db.execute(
        "SELECT * FROM faculty_timetable WHERE faculty_id = ? ORDER BY day_of_week, period_number",
        [uid]
    ).fetchall()

    announcements = db.execute(
        "SELECT * FROM announcements WHERE faculty_id = ? ORDER BY created_at DESC",
        [uid]
    ).fetchall()

    db.close()

    return render_template(
        "faculty_dashboard.html",
        students=students,
        todos=todos,
        timetable_list=timetable_list,
        announcements=announcements,
    )


@app.route("/faculty/add-student", methods=["POST"])
@app.route("/faculty/add_student", methods=["POST"])
def faculty_add_student():
    if session.get("role") != "faculty":
        return redirect(url_for("login"))

    name       = request.form.get("name", "").strip()
    uid_str    = request.form.get("uid", "").strip()
    department = request.form.get("department", "").strip()
    roll       = request.form.get("roll", "").strip()
    password   = request.form.get("password", "").strip()
    cgpa       = float(request.form.get("cgpa", 0) or 0)
    sgpa       = float(request.form.get("sgpa", 0) or 0)
    attendance = int(request.form.get("attendance", 0) or 0)

    if not all([name, uid_str, department, roll, password]):
        flash("All fields are required.", "error")
        return redirect(url_for("faculty_dashboard"))

    try:
        uid = int(uid_str)
    except ValueError:
        flash("UID must be a number.", "error")
        return redirect(url_for("faculty_dashboard"))

    h  = hashlib.sha256(password.encode()).hexdigest()
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (uid, username, password_hash, role, name) VALUES (?,?,?,?,?)",
            (uid, f"student_{uid}", h, "student", name)
        )
        db.execute(
            "INSERT INTO students (uid, department, roll, name, cgpa, sgpa, attendance) VALUES (?,?,?,?,?,?,?)",
            (uid, department, roll, name, cgpa, sgpa, attendance)
        )
        db.commit()
        flash(f"Student '{name}' added successfully.", "success")
    except sqlite3.IntegrityError as e:
        db.rollback()
        flash(f"Error: {e}", "error")
    finally:
        db.close()
    return redirect(url_for("faculty_dashboard"))


@app.route("/faculty/delete-student/<string:roll>", methods=["POST"])
@app.route("/faculty/delete_student/<string:roll>", methods=["POST"])
def faculty_delete_student(roll):
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    db = get_db()
    student = db.execute("SELECT uid FROM students WHERE roll = ?", [roll]).fetchone()
    if student:
        db.execute("DELETE FROM students WHERE roll = ?", [roll])
        db.execute("DELETE FROM users WHERE uid = ?", [student["uid"]])
        db.commit()
        flash("Student deleted.", "info")
    db.close()
    return redirect(url_for("faculty_dashboard"))


# ---------------------------------------------------------------------------
# TIMETABLE ROUTES
# ---------------------------------------------------------------------------

@app.route("/add_timetable", methods=["POST"])
def add_timetable():
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    uid             = session["uid"]
    subject_name    = request.form.get("subject_name", "").strip()
    department_name = request.form.get("department_name", "").strip()
    day_of_week     = request.form.get("day_order", "").strip()
    period_number   = request.form.get("period", 1)

    db = get_db()
    try:
        db.execute(
            "INSERT OR REPLACE INTO faculty_timetable (faculty_id,day_of_week,period_number,subject_name,department_name) VALUES (?,?,?,?,?)",
            (uid, day_of_week, int(period_number), subject_name, department_name)
        )
        db.commit()
        flash("Class added to timetable.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    finally:
        db.close()
    return redirect(url_for("faculty_dashboard"))


@app.route("/edit_timetable/<int:tt_id>", methods=["POST"])
def edit_timetable(tt_id):
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    subject_name    = request.form.get("subject_name", "").strip()
    department_name = request.form.get("department_name", "").strip()
    day_of_week     = request.form.get("day_order", "").strip()
    period_number   = request.form.get("period", 1)
    db = get_db()
    db.execute(
        "UPDATE faculty_timetable SET subject_name=?,department_name=?,day_of_week=?,period_number=? WHERE id=? AND faculty_id=?",
        (subject_name, department_name, day_of_week, int(period_number), tt_id, session["uid"])
    )
    db.commit()
    db.close()
    flash("Class updated.", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/delete_timetable/<int:tt_id>", methods=["POST"])
def delete_timetable(tt_id):
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    db = get_db()
    db.execute("DELETE FROM faculty_timetable WHERE id = ? AND faculty_id = ?", [tt_id, session["uid"]])
    db.commit()
    db.close()
    flash("Class removed.", "info")
    return redirect(url_for("faculty_dashboard"))


# ---------------------------------------------------------------------------
# TO-DO ROUTES
# ---------------------------------------------------------------------------

@app.route("/add_todo", methods=["POST"])
def add_todo():
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    uid             = session["uid"]
    subject_name    = request.form.get("subject_name", "").strip()
    department_name = request.form.get("department_name", "").strip()
    task_date       = request.form.get("task_date", "").strip()
    period          = request.form.get("period", "").strip()

    db = get_db()
    db.execute(
        "INSERT INTO faculty_todos (faculty_id,subject_name,department_name,task_date,period) VALUES (?,?,?,?,?)",
        (uid, subject_name, department_name, task_date, period)
    )
    db.commit()
    db.close()
    flash("Event added.", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/edit_todo/<int:todo_id>", methods=["POST"])
def edit_todo(todo_id):
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    subject_name    = request.form.get("subject_name", "").strip()
    department_name = request.form.get("department_name", "").strip()
    task_date       = request.form.get("task_date", "").strip()
    period          = request.form.get("period", "").strip()
    db = get_db()
    db.execute(
        "UPDATE faculty_todos SET subject_name=?,department_name=?,task_date=?,period=? WHERE id=? AND faculty_id=?",
        (subject_name, department_name, task_date, period, todo_id, session["uid"])
    )
    db.commit()
    db.close()
    flash("Event updated.", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/delete_todo/<int:todo_id>", methods=["POST"])
def delete_todo(todo_id):
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    db = get_db()
    db.execute("DELETE FROM faculty_todos WHERE id = ? AND faculty_id = ?", [todo_id, session["uid"]])
    db.commit()
    db.close()
    flash("Event deleted.", "info")
    return redirect(url_for("faculty_dashboard"))


# ---------------------------------------------------------------------------
# ANNOUNCEMENTS ROUTES
# ---------------------------------------------------------------------------

@app.route("/announcements/add", methods=["POST"])
def add_announcement():
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    title       = request.form.get("title", "").strip()
    message     = request.form.get("message", "").strip()
    target_dept = request.form.get("target_dept", "ALL").strip()

    if not title or not message:
        flash("Title and message are required.", "error")
        return redirect(url_for("faculty_dashboard"))

    db = get_db()
    db.execute(
        "INSERT INTO announcements (faculty_id,faculty_name,title,message,target_dept) VALUES (?,?,?,?,?)",
        (session["uid"], session.get("name", "Faculty"), title, message, target_dept)
    )
    db.commit()
    db.close()
    flash("Announcement posted successfully!", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/announcements/delete/<int:ann_id>", methods=["POST"])
def delete_announcement(ann_id):
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    db = get_db()
    db.execute("DELETE FROM announcements WHERE id = ? AND faculty_id = ?", [ann_id, session["uid"]])
    db.commit()
    db.close()
    flash("Announcement deleted.", "info")
    return redirect(url_for("faculty_dashboard"))


# ---------------------------------------------------------------------------
# NOTES ROUTES
# ---------------------------------------------------------------------------

@app.route("/upload_notes", methods=["GET", "POST"])
def upload_notes():
    if session.get("role") != "faculty":
        return redirect(url_for("login"))

    db = get_db()
    departments = db.execute("SELECT id, name FROM departments ORDER BY name").fetchall()

    if request.method == "POST":
        title         = request.form.get("title", "").strip()
        department_id = request.form.get("department_id", "").strip()
        description   = request.form.get("description", "").strip()
        file          = request.files.get("file")

        if not title or not department_id or not file or not file.filename:
            db.close()
            flash("Title, department and file are all required.", "error")
            return render_template("upload_notes.html", departments=departments)

        if not allowed_file(file.filename):
            db.close()
            flash("File type not allowed.", "error")
            return render_template("upload_notes.html", departments=departments)

        filename  = secure_filename(file.filename)
        save_path = os.path.join(NOTES_FOLDER, filename)
        os.makedirs(NOTES_FOLDER, exist_ok=True)
        file.save(save_path)

        mime  = file.mimetype or "application/octet-stream"
        db.execute(
            """INSERT INTO notes (title,description,file_path,file_name,mime_type,department_id,faculty_id,faculty_name)
               VALUES (?,?,?,?,?,?,?,?)""",
            (title, description, save_path, filename, mime,
             int(department_id), session["uid"], session.get("name", "Faculty"))
        )
        db.commit()
        db.close()
        flash("Notes uploaded successfully!", "success")
        return redirect(url_for("faculty_my_notes"))

    db.close()
    return render_template("upload_notes.html", departments=departments)


@app.route("/faculty_my_notes")
def faculty_my_notes():
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    db = get_db()
    notes = db.execute(
        """SELECT n.id, n.title, n.description, n.file_name, n.uploaded_at, d.name AS department_name
           FROM notes n JOIN departments d ON n.department_id = d.id
           WHERE n.faculty_id = ? ORDER BY n.uploaded_at DESC""",
        [session["uid"]]
    ).fetchall()
    db.close()
    return render_template("faculty_my_notes.html", notes=notes)


@app.route("/view_notes")
def view_notes():
    uid  = session.get("uid")
    role = session.get("role")
    if not uid:
        return redirect(url_for("login"))

    db = get_db()

    if role == "student":
        # get student's department
        student = db.execute("SELECT department FROM students WHERE uid = ?", [uid]).fetchone()
        dept_name = student["department"] if student else None
        dept = db.execute("SELECT id, name FROM departments WHERE name = ?", [dept_name]).fetchone() if dept_name else None
        if dept:
            notes = db.execute(
                """SELECT n.id, n.title, n.description, n.file_name, n.uploaded_at, u.name AS faculty_name
                   FROM notes n JOIN users u ON n.faculty_id = u.uid
                   WHERE n.department_id = ? ORDER BY n.uploaded_at DESC""",
                [dept["id"]]
            ).fetchall()
        else:
            notes = []
    else:
        # Faculty sees all
        dept = None
        notes = db.execute(
            """SELECT n.id, n.title, n.description, n.file_name, n.uploaded_at, u.name AS faculty_name
               FROM notes n JOIN users u ON n.faculty_id = u.uid
               ORDER BY n.uploaded_at DESC"""
        ).fetchall()

    db.close()
    return render_template("view_notes.html", notes=notes, department=dept)


@app.route("/view_note_file/<int:note_id>")
def view_note_file(note_id):
    if not session.get("uid"):
        return redirect(url_for("login"))
    db = get_db()
    note = db.execute("SELECT file_path, file_name, mime_type FROM notes WHERE id = ?", [note_id]).fetchone()
    db.close()
    if not note:
        return "Note not found", 404
    if not os.path.exists(note["file_path"]):
        return "File not found on disk", 404
    return send_file(note["file_path"], mimetype=note["mime_type"] or "application/octet-stream")


@app.route("/download_note/<int:note_id>")
def download_note(note_id):
    if not session.get("uid"):
        return redirect(url_for("login"))
    db = get_db()
    note = db.execute("SELECT file_path, file_name, mime_type FROM notes WHERE id = ?", [note_id]).fetchone()
    db.close()
    if not note:
        return "Note not found", 404
    if not os.path.exists(note["file_path"]):
        return "File not found on disk", 404
    return send_file(note["file_path"], as_attachment=True,
                     download_name=note["file_name"],
                     mimetype=note["mime_type"] or "application/octet-stream")


@app.route("/delete_note/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    db = get_db()
    note = db.execute("SELECT file_path FROM notes WHERE id = ? AND faculty_id = ?",
                      [note_id, session["uid"]]).fetchone()
    if note:
        if os.path.exists(note["file_path"]):
            os.remove(note["file_path"])
        db.execute("DELETE FROM notes WHERE id = ?", [note_id])
        db.commit()
        flash("Note deleted.", "info")
    db.close()
    return redirect(url_for("faculty_my_notes"))


# ---------------------------------------------------------------------------
# PREVIOUS YEAR PAPERS
# ---------------------------------------------------------------------------

@app.route("/previous-year-papers")
@app.route("/previous_year_papers")
def previous_year_papers():
    db     = get_db()
    papers = []
    rows   = db.execute("SELECT * FROM previous_year_papers WHERE approved = 1").fetchall()
    for row in rows:
        paper  = dict(row)
        photos = db.execute(
            "SELECT image_path FROM paper_photos WHERE paper_id = ?", [paper["id"]]
        ).fetchall()
        paper["photos"] = [p["image_path"] for p in photos]
        papers.append(paper)
    db.close()
    return render_template("previous_year_papers.html", papers=papers)


@app.route("/add_paper_grid", methods=["POST"])
def add_paper_grid():
    if session.get("role") != "faculty":
        return redirect(url_for("login"))
    subject     = request.form.get("subject", "Unknown").strip()
    department  = request.form.get("department", "N/A").strip()
    year        = request.form.get("year", 2024)
    semester    = request.form.get("semester", 1)
    no_of_pages = request.form.get("no_of_pages", 0)

    db = get_db()
    db.execute(
        "INSERT INTO previous_year_papers (subject,branch,department,year,semester,no_of_pages,approved) VALUES (?,?,?,?,?,?,0)",
        ("N/A", subject, department, year, semester, no_of_pages)
    )
    db.commit()
    db.close()
    flash("Paper submitted for admin approval.", "success")
    return redirect(url_for("previous_year_papers"))


@app.route("/upload-paper-camera", methods=["POST"])
def upload_paper_camera():
    if not session.get("uid"):
        return jsonify({"success": False, "message": "Login required"})

    paper_id   = request.form.get("paper_id")
    image_data = request.files.get("image")

    if not (image_data and paper_id):
        return jsonify({"success": False, "message": "Missing data"})

    db    = get_db()
    paper = db.execute("SELECT photo_limit FROM previous_year_papers WHERE id = ?", [paper_id]).fetchone()
    count = db.execute("SELECT COUNT(*) as cnt FROM paper_photos WHERE paper_id = ?", [paper_id]).fetchone()

    if paper and count and count["cnt"] >= (paper["photo_limit"] or 1):
        db.close()
        return jsonify({"success": False, "message": f"Maximum photo limit reached."})

    filename = f"paper_{paper_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    filepath = os.path.join(app.static_folder, "images", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    image_data.save(filepath)

    db.execute("INSERT INTO paper_photos (paper_id, image_path) VALUES (?,?)", [paper_id, filename])
    db.commit()
    db.close()
    return jsonify({"success": True, "filename": filename})


# ---------------------------------------------------------------------------
# MISC
# ---------------------------------------------------------------------------

@app.route("/test")
def test():
    try:
        return render_template("test.html")
    except Exception:
        return "Flask is running ✅", 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)