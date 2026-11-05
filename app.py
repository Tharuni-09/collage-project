from flask import Flask, flash, send_file, render_template, request, redirect, session, jsonify
import sqlite3
import hashlib
import os
import re
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle, HRFlowable
from reportlab.lib import colors


def should_print_section(text, user_response):
    """Return True only if a section should be printed."""
    if not text or not text.strip():
        return False
    low = user_response.strip().lower()
    if low in ["no", "false", "0", "none", "not applicable", "na"]:
        return False
    return True


# Make sure static_folder points to `static` next to app.py
app = Flask(__name__,
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key_here")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
app.config['SESSION_COOKIE_PERMANENT']   = True
app.config['SESSION_COOKIE_SECURE']      = False
app.config['SESSION_COOKIE_HTTPONLY']    = True
app.config['SESSION_COOKIE_SAMESITE']   = 'Lax'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "ml_dept.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# AUTO-INIT DATABASE ON STARTUP
# ---------------------------------------------------------------------------
def init_database():
    db = get_db()
    try:
        # Apply base schema if users table doesn't exist yet
        table_exists = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if not table_exists:
            with open(os.path.join(BASE_DIR, "schema.sql"), "r") as f:
                db.executescript(f.read())

        # Ensure all required tables exist (safe to run every time)
        db.execute("""
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
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS paper_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                FOREIGN KEY (paper_id) REFERENCES previous_year_papers(id)
            )
        """)

        db.execute("""
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
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS gallery_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                department TEXT,
                date TEXT,
                photo TEXT NOT NULL,
                approved INTEGER DEFAULT 0,
                faculty_id INTEGER
            )
        """)

        # Safe column migrations for older DB files
        for alter in [
            "ALTER TABLE previous_year_papers ADD COLUMN approved INTEGER DEFAULT 0",
            "ALTER TABLE previous_year_papers ADD COLUMN department TEXT",
            "ALTER TABLE previous_year_papers ADD COLUMN no_of_pages INTEGER DEFAULT 0",
            "ALTER TABLE previous_year_papers ADD COLUMN photo_limit INTEGER DEFAULT 1",
            "ALTER TABLE outreach_programs ADD COLUMN approved INTEGER DEFAULT 0",
            "ALTER TABLE outreach_programs ADD COLUMN department TEXT",
            "ALTER TABLE outreach_programs ADD COLUMN date TEXT",
        ]:
            try:
                db.execute(alter)
            except Exception:
                pass

        db.commit()
    finally:
        db.close()


# Run once at startup
with app.app_context():
    init_database()


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def elaborate(text, section_name):
    """Generate a slightly expanded version of a short section."""
    if not text or section_name not in ["skills", "projects", "internships"]:
        return text

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return ""

    if section_name == "skills":
        bullets = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("python"):
                bullets.append(
                    "Python: Proficient in core Python, OOP, and popular libraries such as NumPy and Pandas."
                )
            elif line.lower().startswith("flask"):
                bullets.append(
                    "Flask: Developed web applications and REST APIs using Flask and SQLite."
                )
            elif line.lower().startswith("machine learning") or "ml" in line.lower():
                bullets.append(
                    "Machine Learning: Experience with classification, regression, and neural networks using scikit‑learn or TensorFlow/PyTorch."
                )
            elif "sql" in line.lower() or "database" in line.lower():
                bullets.append(
                    "SQL & Databases: Designed and queried SQLite and MySQL databases for web applications."
                )
            elif "html" in line.lower() and "css" in line.lower():
                bullets.append(
                    "Web Technologies: Built responsive websites using HTML, CSS, and JavaScript (or frameworks)."
                )
            else:
                bullets.append(f"{line}: Comfortable applying this technology to real‑world projects.")
        return "\n".join(bullets)

    if section_name == "projects":
        bullets = []
        for i, line in enumerate(lines):
            if i == 0 and len(lines) == 1:
                bullets.append(
                    f"{line} – A well‑structured project applying core concepts of the technology stack."
                )
            elif i == 0 and len(lines) > 1:
                bullets.append(f"Project: {line}")
            else:
                bullets.append(f"• {line}")
        return "\n".join(bullets)

    if section_name == "internships":
        bullets = []
        for line in lines:
            if line.strip().lower().startswith("intern") or "internship" in line.lower():
                bullets.append(
                    "Internship role focused on practical software development in a team environment."
                )
            else:
                bullets.append(f"• {line}")
        return "\n".join(bullets)

    return text


def polish_objective(obj):
    """Refine a short career objective into a polished sentence."""
    if not obj.strip():
        return ""
    words = obj.strip().split()
    if not words:
        return ""
    obj = " ".join(words)
    if not obj.endswith("."):
        obj += "."
    return f"Motivated and detail‑oriented professional with strong {obj[0].lower() + obj[1:]}"


# ---------------------------------------------------------------------------
# ROUTES — PUBLIC
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# --- LOGIN ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None)

    uid = request.form.get("uid")
    password = request.form.get("password")
    role = request.form.get("role")

    if not all([uid, password, role]):
        return render_template("login.html", error="Missing fields")

    try:
        uid = int(uid)
    except ValueError:
        return render_template("login.html", error="Invalid UID")

    h = hashlib.sha256(password.encode()).hexdigest()

    db = get_db()
    row = db.execute(
        """
        SELECT
            u.uid, u.username, u.password_hash, u.role, u.name,
            u.email, u.phone
        FROM users u
        WHERE u.uid = ?
        """,
        [uid],
    ).fetchone()
    db.close()

    if not row:
        return render_template("login.html", error="Invalid UID")

    db_uid, username, db_hash, db_role, full_name, email, phone = (
        row["uid"], row["username"], row["password_hash"],
        row["role"], row["name"], row["email"], row["phone"]
    )

    if db_hash != h:
        return render_template("login.html", error="Invalid password")

    if db_role != role:
        return render_template("login.html", error="Role mismatch")

    session["uid"] = db_uid
    session["username"] = username
    session["role"] = db_role
    session["name"] = full_name

    if db_role == "student":
        return redirect("/student-dashboard")
    else:
        return redirect("/faculty-dashboard")


# --- FORGOT PASSWORD ---
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot-password.html", error=None)

    identifier = request.form.get("identifier")
    if not identifier:
        return render_template("forgot-password.html", error="Missing identifier")

    return render_template(
        "forgot-password.html",
        error=None,
        message=f"Reset instructions sent to '{identifier}'."
    )


# ---------------------------------------------------------------------------
# STUDENT ROUTES
# ---------------------------------------------------------------------------

@app.route("/student-dashboard")
def student_dashboard():
    uid = session.get("uid")
    if not uid:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/login")

    db = get_db()

    row = db.execute(
        """
        SELECT
            s.roll, s.name, s.department, s.cgpa, s.sgpa, s.attendance
        FROM students s
        WHERE s.uid = ?
        """,
        [uid],
    ).fetchone()
    if not row:
        db.close()
        return f"Student data not found in students table. UID = {uid}", 404

    roll, name, department, cgpa, sgpa, attendance = (
        row["roll"], row["name"], row["department"],
        row["cgpa"], row["sgpa"], row["attendance"]
    )

    resumes = db.execute(
        """
        SELECT
            r.id, r.uid, r.title, r.pdf_path, r.created_at
        FROM resumes r
        WHERE r.uid = ?
        ORDER BY r.created_at DESC
        """,
        [uid],
    ).fetchall()

    db.close()

    return render_template(
        "student-dashboard.html",
        roll=roll,
        name=name,
        department=department,
        cgpa=cgpa,
        sgpa=sgpa,
        attendance=attendance,
        resumes=resumes,
    )


# --- RESUME FORM (PDF version) ---
@app.route("/resume-form", methods=["GET", "POST"])
def resume_form():
    uid = session.get("uid")
    if not uid:
        return redirect("/login")

    db = get_db()

    user = db.execute(
        """
        SELECT
            u.name, u.email, u.phone
        FROM users u
        WHERE u.uid = ?
        """,
        [uid],
    ).fetchone()
    if not user:
        db.close()
        return "User not found", 404

    name, email, phone = user["name"], user["email"], user["phone"]

    # Form fields
    name_form = phone_form = email_form = linkedin = portfolio = ""
    location = objective = education = technical_skills = soft_skills = ""
    work_experience = internships = projects = certifications = achievements = ""
    extracurriculars = languages = hobbies = references = additional_details = ""
    include_references = ""

    if request.method == "POST":
        name_form          = request.form.get("name", "").strip()
        phone_form         = request.form.get("phone", "").strip()
        email_form         = request.form.get("email", "").strip()
        linkedin           = request.form.get("linkedin", "").strip()
        portfolio          = request.form.get("portfolio", "").strip()
        location           = request.form.get("location", "").strip()
        objective          = request.form.get("objective", "").strip()
        education          = request.form.get("education", "").strip()
        technical_skills   = request.form.get("technical_skills", "").strip()
        soft_skills        = request.form.get("soft_skills", "").strip()
        work_experience    = request.form.get("work_experience", "").strip()
        internships        = request.form.get("internships", "").strip()
        projects           = request.form.get("projects", "").strip()
        certifications     = request.form.get("certifications", "").strip()
        achievements       = request.form.get("achievements", "").strip()
        extracurriculars   = request.form.get("extracurriculars", "").strip()
        languages          = request.form.get("languages", "").strip()
        hobbies            = request.form.get("hobbies", "").strip()
        references         = request.form.get("references", "").strip()
        include_references = request.form.get("include_references", "").strip()
        additional_details = request.form.get("additional_details", "").strip()

        # Update user info
        db.execute(
            "UPDATE users SET email = ?, phone = ? WHERE uid = ?",
            [email_form, phone_form, uid]
        )

        student = db.execute(
            "SELECT id FROM students WHERE uid = ?", [uid]
        ).fetchone()
        if not student:
            db.close()
            return "Student not found", 404

        student_id = student["id"]

        # Generate PDF
        pdf_folder = os.path.join("static", "resumes")
        os.makedirs(pdf_folder, exist_ok=True)

        pdf_name = f"resume_{uid}_{int(datetime.now().timestamp())}.pdf"
        pdf_path = os.path.join(pdf_folder, pdf_name)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
        )

        styles = getSampleStyleSheet()
        styleName = ParagraphStyle(
            name="Name",
            parent=styles["Title"],
            fontSize=16,
            spaceAfter=6,
            alignment=1,
        )
        styleContact = ParagraphStyle(
            name="Contact",
            parent=styles["BodyText"],
            fontSize=10,
            spaceAfter=8,
            alignment=1,
        )
        styleSection = ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6,
        )

        story = []

        name_para = Paragraph(name_form, styleName)
        contact_str = f"{email_form} | {phone_form} | {location}"
        if linkedin:
            contact_str += f" | LinkedIn: {linkedin}"
        if portfolio:
            contact_str += f" | GitHub: {portfolio}"
        contact_para = Paragraph(contact_str, styleContact)

        header_data = [[name_para, contact_para]]
        header = Table(
            header_data,
            colWidths=[A4[0] * 0.6, A4[0] * 0.4],
            hAlign="LEFT"
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(header)
        story.append(HRFlowable(color=colors.black, thickness=0.5))
        story.append(Spacer(1, 8))

        elaborated_objective = polish_objective(objective)
        if elaborated_objective.strip():
            story.append(Paragraph("CAREER OBJECTIVE", styleSection))
            story.append(Paragraph(elaborated_objective, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 10))

        if education.strip():
            story.append(Paragraph("EDUCATION", styleSection))
            story.append(Paragraph(education, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if technical_skills.strip():
            elaborated_skills = elaborate(technical_skills, "skills")
            story.append(Paragraph("TECHNICAL SKILLS", styleSection))
            story.append(Paragraph(elaborated_skills, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if soft_skills.strip():
            story.append(Paragraph("SOFT SKILLS", styleSection))
            story.append(Paragraph(soft_skills, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if work_experience.strip():
            story.append(Paragraph("WORK EXPERIENCE", styleSection))
            story.append(Paragraph(work_experience, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if internships.strip():
            elaborated_internships = elaborate(internships, "internships")
            story.append(Paragraph("INTERNSHIP EXPERIENCE", styleSection))
            story.append(Paragraph(elaborated_internships, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if projects.strip():
            elaborated_projects = elaborate(projects, "projects")
            story.append(Paragraph("PROJECTS", styleSection))
            story.append(Paragraph(elaborated_projects, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if certifications.strip():
            story.append(Paragraph("CERTIFICATIONS", styleSection))
            story.append(Paragraph(certifications, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if achievements.strip():
            story.append(Paragraph("ACHIEVEMENTS / AWARDS", styleSection))
            story.append(Paragraph(achievements, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if extracurriculars.strip():
            story.append(Paragraph("EXTRACURRICULAR ACTIVITIES", styleSection))
            story.append(Paragraph(extracurriculars, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if languages.strip():
            story.append(Paragraph("LANGUAGES", styleSection))
            story.append(Paragraph(languages, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if hobbies.strip():
            story.append(Paragraph("HOBBIES / INTERESTS", styleSection))
            story.append(Paragraph(hobbies, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if should_print_section(references, include_references):
            story.append(Paragraph("REFERENCES", styleSection))
            story.append(Paragraph(references, styles["Normal"]))
            story.append(HRFlowable(color=colors.grey, thickness=0.25))
            story.append(Spacer(1, 8))

        if additional_details.strip():
            story.append(Paragraph("ADDITIONAL DETAILS", styleSection))
            story.append(Paragraph(additional_details, styles["Normal"]))
            story.append(Spacer(1, 8))

        doc.build(story)

        rel_path = f"resumes/{pdf_name}"

        db.execute(
            """
            INSERT INTO resumes (student_id, uid, pdf_path, title, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [student_id, uid, rel_path, "Resume", datetime.now()]
        )

        db.commit()
        db.close()

        return redirect("/student-dashboard")

    # GET
    db.close()
    return render_template(
        "resume-form.html",
        name=name,
        email=email or "",
        phone=phone or "",
        linkedin=linkedin,
        portfolio=portfolio,
        location=location,
        objective=objective,
        education=education,
        technical_skills=technical_skills,
        soft_skills=soft_skills,
        work_experience=work_experience,
        internships=internships,
        projects=projects,
        certifications=certifications,
        achievements=achievements,
        extracurriculars=extracurriculars,
        languages=languages,
        hobbies=hobbies,
        references=references,
        additional_details=additional_details,
    )


# --- DOWNLOAD RESUME ---
@app.route("/download-resume/<int:resume_id>")
def download_resume(resume_id):
    uid = session.get("uid")
    if not uid:
        return "Login required", 401

    db = get_db()
    row = db.execute(
        "SELECT pdf_path FROM resumes WHERE id = ? AND uid = ?",
        [resume_id, uid]
    ).fetchone()
    db.close()

    if not row:
        return "Resume not found", 404

    pdf_path = os.path.join("static", row["pdf_path"])

    if not os.path.exists(pdf_path):
        return "PDF file not found on disk", 404

    return send_file(pdf_path, mimetype="application/pdf")


@app.route("/delete-resume", methods=["POST"])
def delete_resume():
    if "uid" not in session:
        return redirect("/login")

    resume_id = request.form.get("resume_id")
    if not resume_id:
        return "Invalid request", 400

    try:
        resume_id = int(resume_id)
    except ValueError:
        return "Invalid resume ID", 400

    uid = session["uid"]

    db = get_db()

    row = db.execute(
        "SELECT pdf_path FROM resumes WHERE id = ? AND uid = ?",
        [resume_id, uid],
    ).fetchone()

    if not row:
        db.close()
        return "Resume not found", 404

    full_path = os.path.join("static", row["pdf_path"])

    if os.path.exists(full_path):
        os.remove(full_path)

    db.execute("DELETE FROM resumes WHERE id = ? AND uid = ?", [resume_id, uid])
    db.commit()
    db.close()

    return redirect("/student-dashboard")


# ---------------------------------------------------------------------------
# FACULTY ROUTES
# ---------------------------------------------------------------------------

@app.route("/faculty-dashboard")
def faculty_dashboard():
    uid = session.get("uid")
    if not uid or session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()

    students = db.execute(
        """
        SELECT
            s.roll, s.name, s.department, s.cgpa, s.attendance,
            u.username, u.uid
        FROM students s
        JOIN users u ON s.uid = u.uid
        ORDER BY s.department, s.roll
        """
    ).fetchall()

    resumes = db.execute(
        """
        SELECT
            r.id, r.uid, r.title, r.pdf_path, r.created_at
        FROM resumes r
        WHERE r.uid = ?
        ORDER BY r.created_at DESC
        """,
        [uid],
    ).fetchall()

    resumes = [
        {
            "id": row["id"],
            "uid": row["uid"],
            "title": row["title"],
            "pdf_path": row["pdf_path"],
            "created_at": row["created_at"],
        }
        for row in resumes
    ]

    db.close()

    return render_template(
        "faculty-dashboard.html",
        students=students,
        resumes_all=resumes,
    )


@app.route("/faculty/add-student", methods=["POST"])
def faculty_add_student():
    if session.get("role") != "faculty":
        return redirect("/login")

    username   = request.form.get("username")
    password   = request.form.get("password")
    department = request.form.get("department")
    roll       = request.form.get("roll")
    name       = request.form.get("name")
    cgpa       = float(request.form.get("cgpa", 0.0) or 0.0)
    sgpa       = float(request.form.get("sgpa", 0.0) or 0.0)
    attendance = int(request.form.get("attendance", 0) or 0)

    if not all([username, password, department, roll, name]):
        return "Missing required fields", 400

    db = get_db()

    try:
        h = hashlib.sha256(password.encode()).hexdigest()
        db.execute(
            "INSERT INTO users (username, password_hash, name, role) VALUES (?, ?, ?, 'student')",
            [username, h, name],
        )
        db.execute(
            """
            INSERT INTO students (user_id, uid, department, roll, name, cgpa, sgpa, attendance)
            VALUES (
                (SELECT id FROM users WHERE username = ?),
                (SELECT uid FROM users WHERE username = ?),
                ?, ?, ?, ?, ?, ?
            )
            """,
            [username, username, department, roll, name, cgpa, sgpa, attendance],
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        return f"Error: {str(e)}", 400
    finally:
        db.close()

    return redirect("/faculty-dashboard")


@app.route("/faculty/delete-student/<string:roll>", methods=["POST"])
def faculty_delete_student(roll):
    if session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()
    db.execute("DELETE FROM students WHERE roll = ?", [roll])
    db.execute(
        "DELETE FROM users WHERE uid = (SELECT uid FROM students WHERE roll = ?)",
        [roll],
    )
    db.commit()
    db.close()

    return redirect("/faculty-dashboard")


# ---------------------------------------------------------------------------
# PREVIOUS YEAR PAPERS ROUTES
# ---------------------------------------------------------------------------

@app.route("/previous-year-papers")
def previous_year_papers():
    db = get_db()
    papers = []
    papers_rows = db.execute(
        "SELECT * FROM previous_year_papers WHERE approved = 1"
    ).fetchall()
    for row in papers_rows:
        paper = dict(row)
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
        return redirect("/login")

    department  = request.form.get("department", "N/A")
    year        = request.form.get("year", 2024)
    semester    = request.form.get("semester", 1)
    subject     = request.form.get("subject", "Unknown")
    no_of_pages = request.form.get("no_of_pages", 0)

    conn = get_db()
    conn.execute(
        """
        INSERT INTO previous_year_papers (subject, branch, department, year, semester, no_of_pages, approved)
        VALUES (?, 'N/A', ?, ?, ?, ?, 0)
        """,
        (subject, department, year, semester, no_of_pages)
    )
    conn.commit()
    conn.close()

    flash("Paper submitted and is pending admin approval.", "success")
    return redirect("/previous-year-papers")


@app.route("/upload-paper-camera", methods=["POST"])
def upload_paper_camera():
    if not session.get("uid"):
        return jsonify({"success": False, "message": "Login required"})

    paper_id   = request.form.get("paper_id")
    image_data = request.files.get("image")

    if not (image_data and paper_id):
        return jsonify({"success": False, "message": "Missing data"})

    db    = get_db()
    paper = db.execute(
        "SELECT photo_limit FROM previous_year_papers WHERE id = ?", [paper_id]
    ).fetchone()
    current_count = db.execute(
        "SELECT COUNT(*) as count FROM paper_photos WHERE paper_id = ?", [paper_id]
    ).fetchone()

    if paper and current_count["count"] >= paper["photo_limit"]:
        db.close()
        return jsonify({
            "success": False,
            "message": f"Maximum photo limit ({paper['photo_limit']}) reached."
        })

    filename = f"paper_{paper_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    filepath = os.path.join(app.static_folder, "images", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    image_data.save(filepath)

    db.execute(
        "INSERT INTO paper_photos (paper_id, image_path) VALUES (?, ?)",
        [paper_id, filename]
    )
    db.commit()
    db.close()

    return jsonify({"success": True, "filename": filename})


# ---------------------------------------------------------------------------
# MISC ROUTES
# ---------------------------------------------------------------------------

@app.route('/test')
def test():
    return render_template('test.html')


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)