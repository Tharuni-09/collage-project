from flask import Flask, send_file, render_template, request, redirect, session, jsonify
import sqlite3
import hashlib
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "ml_dept.db")

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def should_print_section(text, user_response):
    if not text or not text.strip():
        return False
    low = user_response.strip().lower()
    if low in ["no", "false", "0", "none", "not applicable", "na"]:
        return False
    return True


def elaborate(text, section_name):
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
    if not obj.strip():
        return ""
    words = obj.strip().split()
    if not words:
        return ""
    obj = " ".join(words)
    if not obj.endswith("."):
        obj += "."
    return f"Motivated and detail‑oriented professional with strong {obj[0].lower() + obj[1:]}"


# Expands user input into a fuller, one‑page‑style section
def expand_section(text, section_name):
    if not text or text.lower().strip() in ["no", "none", "na", "false", "0"]:
        return ""

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return ""

    expanded = []

    if section_name == "objective":
        return (
            "Accomplished professional with a background in "
            f"{text}. Dedicated to leveraging technical skills to drive operational "
            "excellence and contribute to organizational success in a challenging role."
        )

    elif section_name == "work_experience":
        for line in lines:
            expanded.append(f"• {line}")
            expanded.append(
                "  - Achieved key deliverables by optimizing workflows and improving "
                "efficiency by 15–20%."
            )
            expanded.append(
                "  - Collaborated with cross‑functional teams to resolve complex "
                "technical challenges."
            )
        return "\n".join(expanded)

    elif section_name == "projects":
        for line in lines:
            expanded.append(f"• Project: {line}")
            expanded.append(
                "  - Developed core architecture using modern frameworks, ensuring "
                "scalability and high performance."
            )
            expanded.append(
                "  - Conducted thorough testing and debugging, resulting in a 10% "
                "improvement in system stability."
            )
        return "\n".join(expanded)

    return "\n".join([f"• {l}" for l in lines])


# =====================================================================
# APP SETUP
# =====================================================================

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)
app.secret_key = "your_secret_key_here"

DB_PATH = "database/ml_dept.db"


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # Auto-create folder
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================================
# INIT DB SCHEMA
# =====================================================================

@app.before_first_request
def init_db():
    db = get_db()
    if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone() is None:
        with open(os.path.join(BASE_DIR, "schema.sql")) as f:
            db.executescript(f.read())
        db.commit()
    db.close()


# =====================================================================
# INDEX AND STATIC PAGES
# =====================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/outreach")
def outreach():
    return render_template("outreach.html")


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/previous-year-papers")
def previous_year_papers():
    return render_template("previous-year-papers.html")  # Create empty HTML later


# =====================================================================
# LOGIN (UID‑BASED)
# =====================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None)

    uid_str = request.form.get("uid")
    password = request.form.get("password")
    role = request.form.get("role")

    if not all([uid_str, password, role]):
        return render_template("login.html", error="Missing fields")

    try:
        uid = int(uid_str)
    except ValueError:
        return render_template("login.html", error="Invalid UID")

    h = hashlib.sha256(password.encode()).hexdigest()

    db = get_db()
    row = db.execute(
        """
        SELECT
            uid, username, password_hash, role, name, email, phone
        FROM
            users
        WHERE
            uid = ?
        """,
        [uid]
    ).fetchone()
    db.close()

    if not row:
        print(f"DEBUG: No user found for UID: {uid}")
        return render_template("login.html", error="Invalid UID - No such user found")

    db_uid, username, db_hash, db_role, full_name, email, phone = row

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


# =====================================================================
# FORGOT PASSWORD (STUB)
# =====================================================================

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


# =====================================================================
# STUDENT DASHBOARD
# =====================================================================

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
        FROM
            students s
        WHERE
            s.uid = ?
        """,
        [uid]
    ).fetchone()
    if not row:
        db.close()
        return render_template(
            "student-dashboard.html",
            roll="N/A",
            name="Unknown Student",
            department="N/A",
            cgpa=0,
            sgpa=0,
            attendance=0,
            resumes=[],
            error="Student profile not found. Please contact the administrator.",
        ), 404

    roll, name, department, cgpa, sgpa, attendance = row

    resumes = db.execute(
        """
        SELECT
            r.id, r.uid, r.title, r.pdf_path, r.created_at
        FROM
            resumes r
        WHERE
            r.uid = ?
        ORDER BY
            r.created_at DESC
        """,
        [uid]
    ).fetchall()
    db.close()

    return render_template(
        "student-dashboard.html",
        roll=roll, name=name, department=department,
        cgpa=cgpa, sgpa=sgpa, attendance=attendance,
        resumes=resumes,
        session=session  # ← ADD THIS
    )


# =====================================================================
# FACULTY DEPARTMENT / RESUMES PAGES

@app.route("/debug-dashboard")
def debug_dashboard():
    uid = session.get("uid")
    if not uid or session.get("role") != "faculty":
        return "Login as faculty first"
    
    try:
        db = get_db()
        students_ncsml = db.execute("SELECT * FROM students WHERE department = 'NCSML'").fetchall()
        print("First NCSML student keys:", students_ncsml[0].keys() if students_ncsml else "NO DATA")
        print("First student type:", type(students_ncsml[0]) if students_ncsml else "EMPTY")
        db.close()
        return f"NCSML students: {len(students_ncsml)}<br>Type: {type(students_ncsml[0]) if students_ncsml else 'empty'}"
    except Exception as e:
        import traceback
        return f"ERROR: {str(e)}<br>{traceback.format_exc()}"


@app.route("/faculty-dashboard")
def faculty_dashboard():
    try:
        uid = session.get("uid")
        if not uid or session.get("role") != "faculty":
            return redirect("/login")

        db = get_db()
        
        students_acsml = db.execute("SELECT * FROM students WHERE department = 'ACSML'").fetchall()
        students_ncsml = db.execute("SELECT * FROM students WHERE department = 'NCSML'").fetchall()
        students_dcsml = db.execute("SELECT * FROM students WHERE department = 'DCSML'").fetchall()
        
        resumes_acsml = db.execute("""
            SELECT r.id, r.uid, r.title, r.pdf_path, r.created_at, s.roll, s.name 
            FROM resumes r JOIN students s ON r.uid = s.uid 
            WHERE s.department = 'ACSML'
        """).fetchall()
        
        resumes_ncsml = db.execute("""
            SELECT r.id, r.uid, r.title, r.pdf_path, r.created_at, s.roll, s.name 
            FROM resumes r JOIN students s ON r.uid = s.uid 
            WHERE s.department = 'NCSML'
        """).fetchall()
        
        resumes_dcsml = db.execute("""
            SELECT r.id, r.uid, r.title, r.pdf_path, r.created_at, s.roll, s.name 
            FROM resumes r JOIN students s ON r.uid = s.uid 
            WHERE s.department = 'DCSML'
        """).fetchall()
        
        db.close()

        return render_template("faculty-dashboard.html", 
                             students_acsml=students_acsml,
                             students_ncsml=students_ncsml,
                             students_dcsml=students_dcsml,
                             resumes_acsml=resumes_acsml,
                             resumes_ncsml=resumes_ncsml,
                             resumes_dcsml=resumes_dcsml,
                             session=session)
                             
    except Exception as e:
        import traceback
        error_msg = f"ERROR: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)  # Terminal
        return f"<pre>{error_msg}</pre>"  # Browser shows exact error

@app.route("/faculty/resumes")
def faculty_resumes():
    uid = session.get("uid")
    if not uid or session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()
    db.row_factory = sqlite3.Row
    resumes = db.execute(
        """
        SELECT r.id, r.uid, r.title, r.pdf_path, r.created_at, s.roll, s.name, s.department
        FROM resumes r
        JOIN students s ON r.uid = s.uid
        ORDER BY r.created_at DESC
        """
    ).fetchall()
    db.close()

    return render_template("faculty-resumes.html", resumes=resumes)


# =====================================================================
# FACULTY ADD STUDENT
# =====================================================================
@app.route("/resume-form", methods=["GET", "POST"])
def resume_form():
    uid = session.get("uid")
    if not uid:
        return redirect("/login")

    db = get_db()
    student = db.execute("SELECT roll FROM students WHERE uid = ?", [uid]).fetchone()
    db.close()

    if not student:
        return "Student profile not found", 404

    if request.method == "POST":
        pdf_folder = os.path.join(app.static_folder, "resumes")
        os.makedirs(pdf_folder, exist_ok=True)

        pdf_name = f"resume_{uid}_{int(datetime.now().timestamp())}.pdf"
        pdf_path_disk = os.path.join("resumes", pdf_name)
        full_path = os.path.join(pdf_folder, pdf_name)

        doc = SimpleDocTemplate(
            full_path,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        styles = getSampleStyleSheet()
        styleName = ParagraphStyle(
            "Name", parent=styles["Title"], fontSize=24, leading=28, spaceAfter=15
        )
        styleSection = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.darkblue
        )
        styleNormal = ParagraphStyle(
            "Normal", parent=styles["Normal"], fontSize=10, leading=14
        )

        story = []
        story.append(Paragraph(request.form.get("name", ""), styleName))
        story.append(
            Paragraph(
                f"{request.form.get('email', '')} | "
                f"{request.form.get('phone', '')} | "
                f"{request.form.get('location', '')}",
                styles["BodyText"]
            )
        )
        story.append(Spacer(1, 10))
        story.append(
            HRFlowable(color=colors.black, thickness=1, width="100%")
        )

        left_col = [
            Paragraph("PROFESSIONAL SUMMARY", styleSection),
            Paragraph(expand_section(request.form.get("objective", ""), "objective"), styleNormal),
            Paragraph("WORK HISTORY", styleSection),
            Paragraph(expand_section(request.form.get("work_experience", ""), "work_experience"), styleNormal),
            Paragraph("PROJECTS", styleSection),
            Paragraph(expand_section(request.form.get("projects", ""), "projects"), styleNormal),
        ]
        right_col = [
            Paragraph("SKILLS", styleSection),
            Paragraph(expand_section(request.form.get("technical_skills", ""), "technical_skills"), styleNormal),
            Paragraph("CERTIFICATIONS", styleSection),
            Paragraph(expand_section(request.form.get("certifications", ""), "certifications"), styleNormal),
            Paragraph("EDUCATION", styleSection),
            Paragraph(expand_section(request.form.get("education", ""), "education"), styleNormal),
        ]

        table = Table(
            [[left_col, right_col]],
            colWidths=[A4[0] * 0.60, A4[0] * 0.35]
        )
        table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
        story.append(table)

        doc.build(story)

        student_id = student[0]
        conn = get_db()
        conn.execute(
            "INSERT INTO resumes (student_id, uid, pdf_path, title, created_at) VALUES (?, ?, ?, ?, ?)",
            [student_id, uid, pdf_path_disk, "Resume", datetime.now()]
        )
        conn.commit()
        conn.close()

        return redirect("/student-dashboard")

    return render_template("resume-form.html")
# =====================================================================
# DOWNLOAD / VIEW RESUME
# =====================================================================

@app.route("/download-resume/<int:resume_id>")
def download_resume(resume_id):
    db = get_db()
    row = db.execute(
        "SELECT pdf_path FROM resumes WHERE id = ?",
        [resume_id]
    ).fetchone()
    db.close()

    if not row:
        return "Resume not found in database", 404

    pdf_path_in_db = row[0]  # e.g. 'resumes/resume_1_...'
    full_path = os.path.join(app.static_folder, pdf_path_in_db)
    print("FULL PATH:", full_path)

    if not os.path.exists(full_path):
        print("FILE NOT EXIST:", full_path)
        return "PDF file not found on disk", 404

    return send_file(full_path, mimetype="application/pdf")


@app.route("/view-resume/<int:resume_id>")
def view_resume(resume_id):
    # Allow faculty to view any resume, students only their own
    if session.get("role") == "faculty":
        db = get_db()
        row = db.execute(
            "SELECT pdf_path FROM resumes WHERE id = ?",
            [resume_id]
        ).fetchone()
        db.close()
    else:
        db = get_db()
        row = db.execute(
            "SELECT pdf_path FROM resumes WHERE id = ? AND uid = ?",
            [resume_id, session.get("uid")]
        ).fetchone()
        db.close()

    if not row:
        return "Resume not found", 404

    pdf_path_in_db = row[0]
    full_path = os.path.join(app.static_folder, pdf_path_in_db)

    if not os.path.exists(full_path):
        return "PDF file not found on disk", 404

    return send_file(full_path, mimetype="application/pdf")


# =====================================================================
# DELETE RESUME
# =====================================================================

@app.route("/delete-resume", methods=["POST"])
def delete_resume():
    if "uid" not in session:
        return redirect("/login")

    resume_id_str = request.form.get("resume_id")
    if not resume_id_str:
        return "Invalid request", 400

    try:
        resume_id = int(resume_id_str)
    except ValueError:
        return "Invalid resume ID", 400

    uid = session["uid"]
    db = get_db()

    # Get file path before deleting
    row = db.execute(
        "SELECT pdf_path FROM resumes WHERE id = ? AND uid = ?",
        [resume_id, uid]
    ).fetchone()

    if not row:
        db.close()
        return "Resume not found", 404

    pdf_path_in_db = row[0]
    pdf_path_on_disk = os.path.join("static", pdf_path_in_db)

    # Delete file if it exists
    if os.path.exists(pdf_path_on_disk):
        os.remove(pdf_path_on_disk)

    # Delete row from DB
    db.execute("DELETE FROM resumes WHERE id = ? AND uid = ?", [resume_id, uid])
    db.commit()
    db.close()

    return redirect("/student-dashboard")


# =====================================================================
# FACULTY DASHBOARD + ALL RESUMES
# =====================================================================

@app.route("/faculty-dashboard")
def faculty_dashboard():
    uid = session.get("uid")
    if not uid or session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()
    db.row_factory = sqlite3.Row
    
    # Get students by department
    students_acsml = db.execute("SELECT * FROM students WHERE department = 'ACSML'").fetchall()
    students_ncsml = db.execute("SELECT * FROM students WHERE department = 'NCSML'").fetchall()
    students_dcsml = db.execute("SELECT * FROM students WHERE department = 'DCSML'").fetchall()
    
    # Get resumes by department
    resumes_acsml = db.execute(
        """
        SELECT
            r.id, r.uid, r.title, r.pdf_path, r.created_at,
            s.roll, s.name, s.department
        FROM
            resumes r
        JOIN
            students s ON r.uid = s.uid
        WHERE s.department = 'ACSML'
        ORDER BY
            r.created_at DESC
        """
    ).fetchall()
    
    resumes_ncsml = db.execute(
        """
        SELECT
            r.id, r.uid, r.title, r.pdf_path, r.created_at,
            s.roll, s.name, s.department
        FROM
            resumes r
        JOIN
            students s ON r.uid = s.uid
        WHERE s.department = 'NCSML'
        ORDER BY
            r.created_at DESC
        """
    ).fetchall()
    
    resumes_dcsml = db.execute(
        """
        SELECT
            r.id, r.uid, r.title, r.pdf_path, r.created_at,
            s.roll, s.name, s.department
        FROM
            resumes r
        JOIN
            students s ON r.uid = s.uid
        WHERE s.department = 'DCSML'
        ORDER BY
            r.created_at DESC
        """
    ).fetchall()
    
    db.close()

    return render_template("faculty-dashboard.html",
                       students_acsml=students_acsml,
                       students_ncsml=students_ncsml,
                       students_dcsml=students_dcsml,
                       resumes_acsml=resumes_acsml,
                       resumes_ncsml=resumes_ncsml,
                       resumes_dcsml=resumes_dcsml,
                       session=session)


# =====================================================================
# FACULTY ADD STUDENT
# =====================================================================
@app.route("/faculty/add-student", methods=["POST"])
def faculty_add_student():
    if session.get("role") != "faculty":
        return redirect("/login")

    username = request.form.get("username")
    password = request.form.get("password")
    department = request.form.get("department")
    roll = request.form.get("roll")
    name = request.form.get("name")
    cgpa = float(request.form.get("cgpa", 0.0) or 0.0)
    sgpa = float(request.form.get("sgpa", 0.0) or 0.0)
    attendance = int(request.form.get("attendance", 0) or 0)

    if not all([username, password, department, roll, name]):
        return "Missing required fields", 400

    db = get_db()

    try:
        h = hashlib.sha256(password.encode()).hexdigest()

        # 1. Insert into users
        db.execute(
            "INSERT INTO users (username, password_hash, name, role) VALUES (?, ?, ?, 'student')",
            [username, h, name]
        )
        db.commit()

        # 2. Now get the new user's uid
        user_row = db.execute(
            "SELECT uid FROM users WHERE username = ?", [username]
        ).fetchone()
        if not user_row:
            db.rollback()
            return "User creation failed", 500

        uid = user_row[0]

        # 3. Insert into students
        db.execute(
            """
            INSERT INTO students (uid, department, roll, name, cgpa, sgpa, attendance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [uid, department, roll, name, cgpa, sgpa, attendance]
        )
        db.commit()

    except sqlite3.IntegrityError as e:
        db.rollback()
        return f"Error: {str(e)}", 400
    except Exception as e:
        db.rollback()
        return f"Unexpected error: {str(e)}", 500
    finally:
        db.close()

    return redirect("/faculty-dashboard")

@app.route("/faculty/delete-student/<string:roll>", methods=["POST"])
def faculty_delete_student(roll):
    if session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()
    row = db.execute("SELECT uid FROM students WHERE roll = ?", [roll]).fetchone()
    if row:
        uid = row[0]
        db.execute("DELETE FROM resumes WHERE uid = ?", [uid])
        db.execute("DELETE FROM students WHERE roll = ?", [roll])
        db.execute("DELETE FROM users WHERE uid = ?", [uid])
        db.commit()
    db.close()

    return redirect("/faculty-dashboard")

@app.route("/student-details/<int:student_uid>")
def student_details(student_uid):
    if session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()
    db.row_factory = sqlite3.Row
    
    # Get student details
    student = db.execute("SELECT * FROM students WHERE uid = ?", [student_uid]).fetchone()
    
    if not student:
        db.close()
        return "Student not found", 404
    
    # Get student's resumes
    resumes = db.execute(
        "SELECT * FROM resumes WHERE uid = ? ORDER BY created_at DESC",
        [student_uid]
    ).fetchall()
    
    db.close()
    
    return render_template("student-details.html", student=student, resumes=resumes)

@app.route("/test")
def test():
    return render_template("test.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip().lower()
    if not user_msg:
        return jsonify({"reply": "Please type a message."})

    # Enhanced chat responses based on keywords
    responses = {
        "hello": "Hello! Welcome to the ML Department portal. How can I help you today?",
        "hi": "Hi there! I'm here to assist you with information about our department.",
        "help": "I can help you with information about:\n• Department programs (ACSML, NCSML, DCSML)\n• Faculty information\n• Student resources\n• Resume building\n• Academic information\n• Contact details\n\nWhat would you like to know?",
        "department": "We offer three specialized programs:\n• ACSML: Applied Computer Science and Machine Learning\n• NCSML: Neural Computing and Systems Machine Learning\n• DCSML: Data Science and Computational Machine Learning\n\nEach program focuses on cutting-edge AI and ML technologies.",
        "faculty": "Our faculty includes experienced professors specializing in AI, Machine Learning, Data Science, and Computer Science. You can view their profiles on the Faculty section of our homepage.",
        "student": "As a student, you can:\n• Build and manage your resume\n• View your academic performance\n• Access department resources\n• Download your submitted resumes\n\nLogin to your student dashboard for full access.",
        "resume": "Our resume builder helps you create professional resumes with:\n• Personal information\n• Academic details\n• Skills and projects\n• Work experience\n• Professional formatting\n\nYou can generate PDFs and download them anytime.",
        "contact": "You can reach us at:\n• Email: info@ml-dept.edu\n• Phone: +91-9876543210\n• Address: Loyola Academy, Old Alwal, Secunderabad\n\nVisit our contact section for more details.",
        "admission": "For admissions, visit our college website or contact the admissions office. We offer undergraduate programs in Computer Science with Machine Learning specializations.",
        "placement": "Our department has excellent placement records with top companies in AI/ML, Tech, and Data Science. Students receive training in industry-relevant skills.",
        "project": "Students work on real-world projects in:\n• Machine Learning algorithms\n• Data analysis\n• AI applications\n• Web development\n• Research projects\n\nMany projects lead to publications and internships.",
        "thank": "You're welcome! Feel free to ask if you need any more information.",
        "bye": "Goodbye! Have a great day. Visit us again soon.",
        "goodbye": "Goodbye! Stay connected with our department.",
    }

    # Check for keywords in user message
    for keyword, response in responses.items():
        if keyword in user_msg:
            return jsonify({"reply": response})

    # Default responses for common queries
    if any(word in user_msg for word in ["what", "how", "when", "where", "why", "who"]):
        return jsonify({"reply": "I'd be happy to help with that information. Could you please be more specific about what you're looking for? You can ask about our programs, faculty, admissions, or any other department-related topics."})

    if any(word in user_msg for word in ["login", "password", "account"]):
        return jsonify({"reply": "For login issues or account help, please contact the department administrator or check the login page for instructions. Default password for demo accounts is '123456'."})

    # Generic helpful response
    return jsonify({"reply": "I'm here to help with information about the Machine Learning Department. You can ask me about our programs, faculty, student resources, or any other department-related questions. What would you like to know?"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
