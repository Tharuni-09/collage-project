from flask import Flask, send_file, render_template, request, redirect, session, current_app, jsonify
import sqlite3
import hashlib
import os
import re
from flask import url_for
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Flowable,
    HRFlowable,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfform


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


COMMON_SPELLING_FIXES = {
    "oblective": "objective",
    "doutd": "doubt",
    "recieve": "receive",
    "teh": "the",
    "adn": "and",
    "acheivement": "achievement",
    "deatils": "details",
    "develpment": "development",
    "manger": "manager",
    "projct": "project",
    "programe": "program",
    "speling": "spelling",
    "currect": "correct",
}


def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    for wrong, right in COMMON_SPELLING_FIXES.items():
        text = re.sub(rf"\b{wrong}\b", right, text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text


def enhance_objective(objective, field_of_study):
    objective = clean_text(objective)
    if not objective:
        field = field_of_study or "student"
        return f"Motivated {field.lower()} seeking opportunities to apply strong technical skills in data science, machine learning, and software development."

    objective = polish_objective(objective)
    if len(objective.split()) < 15:
        objective = objective.rstrip('.')
        objective += ", eager to contribute to data-driven projects and innovative teams."
    return objective


def parse_projects(projects_text):
    if not projects_text or not projects_text.strip():
        return []
    return [clean_text(line) for line in projects_text.splitlines() if line.strip()]


def describe_project(project_line):
    text = project_line.strip()
    lower = text.lower()
    bullets = []

    # Project-specific intelligent descriptions
    if any(word in lower for word in ["recommendation", "recommender"]):
        bullets.append("Implemented collaborative filtering and content-based algorithms.")
        bullets.append("Achieved 85%+ accuracy using matrix factorization techniques.")
        bullets.append("Designed personalized recommendation engine with real-time predictions.")
    elif any(word in lower for word in ["sentiment", "emotion", "opinion"]):
        bullets.append("Built NLP pipeline for sentiment analysis with text preprocessing.")
        bullets.append("Trained classifiers with 90%+ accuracy on labeled datasets.")
        bullets.append("Deployed model for real-time social media monitoring.")
    elif any(word in lower for word in ["image", "vision", "cnn", "object detection"]):
        bullets.append("Designed CNN architecture using TensorFlow/PyTorch.")
        bullets.append("Applied data augmentation and transfer learning techniques.")
        bullets.append("Achieved 92%+ accuracy on image classification benchmarks.")
    elif any(word in lower for word in ["chatbot", "conversational", "nlp"]):
        bullets.append("Built NLP pipeline for intent recognition and response generation.")
        bullets.append("Integrated with Flask backend for multi-turn dialogue capability.")
        bullets.append("Deployed with context awareness and 95%+ user satisfaction.")
    elif any(word in lower for word in ["forecasting", "prediction", "time series"]):
        bullets.append("Applied ARIMA and Prophet models for time-series forecasting.")
        bullets.append("Achieved RMSE of 5-8% on validation datasets.")
        bullets.append("Built interactive dashboards for trend visualization and insights.")
    elif any(word in lower for word in ["clustering", "segmentation"]):
        bullets.append("Implemented K-means, DBSCAN, and hierarchical clustering.")
        bullets.append("Optimized using silhouette analysis and elbow method.")
        bullets.append("Discovered actionable customer segments improving ROI by 25%.")
    elif any(word in lower for word in ["web", "flask", "django", "frontend", "backend"]):
        bullets.append("Built full-stack web application with responsive UI and scalable backend.")
        bullets.append("Implemented authentication, database management, and REST APIs.")
        bullets.append("Deployed with Docker and integrated GitHub CI/CD pipeline.")
    elif any(word in lower for word in ["machine learning", "ml", "deep learning", "neural"]):
        bullets.append("Designed and trained ML models for real-world problem solving.")
        bullets.append("Implemented data preprocessing, feature engineering, and model evaluation.")
        bullets.append("Optimized hyperparameters achieving 88%+ accuracy on test data.")
    elif any(word in lower for word in ["automation", "script", "tool", "pipeline"]):
        bullets.append("Automated critical workflows improving productivity by 40%+.")
        bullets.append("Developed robust scripts with error handling and monitoring.")
        bullets.append("Documented thoroughly for easy maintenance and scalability.")
    else:
        bullets.append("Developed a practical solution with focus on usability and performance.")
        bullets.append("Implemented core features using industry best practices and design patterns.")
        bullets.append("Tested rigorously and optimized for production deployment.")

    return bullets


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
    return render_template("previous-year-papers.html", session=session)


# =====================================================================
# LOGIN (UID‑BASED)
# =====================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None)

    uid = request.form.get("uid")
    password = request.form.get("password")
    role = request.form.get("role")

    if not all([uid, password, role]):
        return render_template("login.html", error="Missing fields")

    h = hashlib.sha256(password.encode()).hexdigest()

    db = get_db()
    if role == "student":
        row = db.execute(
            """
            SELECT
                u.uid, u.username, u.password_hash, u.role, u.name, u.email, u.phone
            FROM users u
            JOIN students s
                ON u.uid = s.uid
            WHERE
                u.uid = ?
                OR s.roll = ?
            """,
            [uid, uid]
        ).fetchone()
    else:
        # Allow faculty to login using uid OR username OR email
        row = db.execute(
            """
            SELECT
                u.uid, u.username, u.password_hash, u.role, u.name, u.email, u.phone
            FROM users u
            WHERE
                (u.uid = ? OR u.username = ? OR u.email = ?)
                AND u.role = 'faculty'
            """,
            [uid, uid, uid]
        ).fetchone()
    db.close()

    if not row:
        return render_template("login.html", error="Invalid UID - No such user found")

    db_uid = row["uid"]
    username = row["username"]
    db_hash = row["password_hash"]
    db_role = row["role"]
    full_name = row["name"]
    email = row["email"]
    phone = row["phone"]

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
# FORGOT PASSWORD
# =====================================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forget-password.html", error=None, step="request")

    action = request.form.get("action", "request")
    if action == "request":
        identifier = clean_text(request.form.get("identifier", ""))
        if not identifier:
            return render_template("forget-password.html", error="Missing identifier", step="request")

        db = get_db()
        row = db.execute(
            """
            SELECT u.uid, u.email, u.phone, s.roll
            FROM users u
            LEFT JOIN students s ON u.uid = s.uid
            WHERE u.uid = ? OR u.email = ? OR u.phone = ? OR s.roll = ?
            """,
            [identifier, identifier, identifier, identifier]
        ).fetchone()
        db.close()

        if not row:
            return render_template(
                "forget-password.html",
                error="No user found with that UID, email, phone, or roll number.",
                step="request"
            )

        user_email = row["email"] if isinstance(row, sqlite3.Row) else row[1]
        if not user_email:
            return render_template(
                "forget-password.html",
                error="No email address is available for this account.",
                step="request"
            )

        return render_template(
            "forget-password.html",
            step="reset",
            uid=row["uid"],
            email=user_email,
            message=f"A reset email would be sent to {user_email}. Enter your new password below."
        )

    if action == "reset":
        uid = request.form.get("uid")
        email = clean_text(request.form.get("email", ""))
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not all([uid, email, password, password_confirm]):
            return render_template(
                "forget-password.html",
                error="All fields are required.",
                step="reset",
                uid=uid,
                email=email
            )

        if password != password_confirm:
            return render_template(
                "forget-password.html",
                error="Passwords do not match.",
                step="reset",
                uid=uid,
                email=email
            )

        db = get_db()
        row = db.execute(
            "SELECT email FROM users WHERE uid = ?",
            [uid]
        ).fetchone()
        if not row or (row["email"] if isinstance(row, sqlite3.Row) else row[0]) != email:
            db.close()
            return render_template(
                "forget-password.html",
                error="Email verification failed.",
                step="request"
            )

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        db.execute(
            "UPDATE users SET password_hash = ? WHERE uid = ?",
            [password_hash, uid]
        )
        db.commit()
        db.close()

        return render_template(
            "forget-password.html",
            message="Password reset successfully. You can now login with your new password.",
            step="done"
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
# Debug 
# =====================================================================
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

# =====================================================================
# FACULTY DASHBOARD
# =====================================================================
@app.route("/faculty/<dept>")
def faculty_department(dept):
    if session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()
    students = db.execute(
        "SELECT * FROM students WHERE department = ? ORDER BY roll",
        [dept]
    ).fetchall()
    resumes = db.execute(
        """
        SELECT r.id, r.uid, r.title, r.pdf_path, r.created_at,
               s.roll, s.name
        FROM resumes r
        JOIN students s ON r.uid = s.uid
        WHERE s.department = ?
        ORDER BY s.roll
        """,
        [dept]
    ).fetchall()
    db.close()

    return render_template(
        "faculty-department.html",
        department=dept,
        students=students,
        resumes=resumes,
        session=session
    )


@app.route("/faculty-dashboard")
def faculty_dashboard():
    try:
        uid = session.get("uid")
        if not uid or session.get("role") != "faculty":
            return redirect("/login")

        dept = request.args.get("dept", None)  # from URL: ?dept=ACSML

        db = get_db()

        def get_students_for(department):
            if dept is None or dept == department:
                return db.execute(
                    "SELECT * FROM students WHERE department = ? ORDER BY roll",
                    [department]
                ).fetchall()
            return []

        def get_resumes_for(department):
            if dept is None or dept == department:
                return db.execute(
                    """
                    SELECT r.id, r.uid, r.title, r.pdf_path, r.created_at,
                           s.roll, s.name
                    FROM resumes r
                    JOIN students s ON r.uid = s.uid
                    WHERE s.department = ?
                    ORDER BY s.roll
                    """,
                    [department]
                ).fetchall()
            return []

        students_acsml = get_students_for("ACSML")
        students_ncsml = get_students_for("NCSML")
        students_dcsml = get_students_for("DCSML")

        resumes_acsml = get_resumes_for("ACSML")
        resumes_ncsml = get_resumes_for("NCSML")
        resumes_dcsml = get_resumes_for("DCSML")

        db.close()

        return render_template("faculty-dashboard.html",
                             students_acsml=students_acsml,
                             students_ncsml=students_ncsml,
                             students_dcsml=students_dcsml,
                             resumes_acsml=resumes_acsml,
                             resumes_ncsml=resumes_ncsml,
                             resumes_dcsml=resumes_dcsml,
                             session=session,
                             dept=dept)

    except Exception as e:
        import traceback
        error_msg = f"ERROR: {str(e)}\\n\\n{traceback.format_exc()}"
        print(error_msg)
        return f"<pre>{error_msg}</pre>"

# =====================================================================
# EDIT STUDENT DETAILS - FACULTY DASHBOARD
# =====================================================================
@app.route("/faculty/edit-student/<int:uid>", methods=["GET", "POST"])
def faculty_edit_student(uid):
    if session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()

    if request.method == "GET":
        student = db.execute(
            """
            SELECT uid, roll, name, department, cgpa, sgpa, attendance
            FROM students
            WHERE uid = ?
            """,
            [uid]
        ).fetchone()
        if not student:
            db.close()
            return "Student not found", 404

        db.close()
        return render_template("faculty-edit-student.html", student=student)

    # POST
    department = request.form.get("department")
    roll = request.form.get("roll")
    name = request.form.get("name")
    cgpa = float(request.form.get("cgpa", 0.0) or 0.0)
    sgpa = float(request.form.get("sgpa", 0.0) or 0.0)
    attendance = int(request.form.get("attendance", 0) or 0)
    

    if not all([department, roll, name]):
        db.close()
        return "Missing required fields", 400

    try:
        db.execute(
            """
            UPDATE students
            SET department = ?, roll = ?, name = ?, cgpa = ?, sgpa = ?, attendance = ?
            WHERE uid = ?
            """,
            [department, roll, name, cgpa, sgpa, attendance, uid]
        )
        db.commit()
    except Exception as e:
        db.rollback()
        return f"Error updating student: {str(e)}", 500
    finally:
        db.close()

    return redirect("/faculty-dashboard")


# =====================================================================
# FACULTY ADD STUDENT PAGE
# =====================================================================
@app.route("/faculty/add-student", methods=["GET"])
def faculty_add_student_form():

    if session.get("role") != "faculty":
        return redirect("/login")

    return render_template("faculty-add-student.html")


# =====================================================================
# FACULTY ADD STUDENT SAVE
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

    email = request.form.get("email")
    phone = request.form.get("phone")

    cgpa = float(request.form.get("cgpa", 0.0) or 0.0)
    sgpa = float(request.form.get("sgpa", 0.0) or 0.0)
    attendance = int(request.form.get("attendance", 0) or 0)

    if not all([username, password, department, roll, name]):
        return "Missing required fields", 400

    db = get_db()

    try:
        h = hashlib.sha256(password.encode()).hexdigest()

        db.execute(
            """
            INSERT INTO users
            (username, password_hash, name, role, email, phone)
            VALUES (?, ?, ?, 'student', ?, ?)
            """,
            [username, h, name, email, phone]
        )

        db.commit()

        user_row = db.execute(
            "SELECT uid FROM users WHERE username = ?",
            [username]
        ).fetchone()

        uid = user_row[0]

        db.execute(
            """
            INSERT INTO students
            (uid, department, roll, name, cgpa, sgpa, attendance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [uid, department, roll, name, cgpa, sgpa, attendance]
        )

        db.commit()

    except Exception as e:
        db.rollback()
        return str(e)

    finally:
        db.close()

    return redirect("/faculty-dashboard")
# =====================================================================
# FACULTY DELETE STUDENT SAVE
# =====================================================================

@app.route("/faculty/delete-student/<string:roll>", methods=["POST"])
def faculty_delete_student(roll):

    if session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()

    row = db.execute(
        "SELECT uid FROM students WHERE roll = ?",
        [roll]
    ).fetchone()

    if row:
        uid = row[0]

        db.execute(
            "DELETE FROM resumes WHERE uid = ?",
            [uid]
        )

        db.execute(
            "DELETE FROM students WHERE roll = ?",
            [roll]
        )

        db.execute(
            "DELETE FROM users WHERE uid = ?",
            [uid]
        )

        db.commit()

    db.close()

    return redirect("/faculty-dashboard")



# =====================================================================
# RESUME TEMPLATE GENERATORS (5 Styles)
# =====================================================================

def generate_resume_pdf(template_type, form_data, student, full_pdf_path):
    """Generate resume in selected template style"""
    
    doc = SimpleDocTemplate(
        full_pdf_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=35,
        bottomMargin=35
    )
    
    styles = getSampleStyleSheet()
    
    # Template-specific styling
    template_colors = {
        "classic": {"primary": "#111827", "secondary": "#4b5563", "accent": "#d1d5db"},
        "modern": {"primary": "#0066cc", "secondary": "#1a7b3d", "accent": "#e8f0fe"},
        "minimal": {"primary": "#000000", "secondary": "#666666", "accent": "#cccccc"},
        "academic": {"primary": "#1b3399", "secondary": "#2d5a8c", "accent": "#d9e3f0"},
        "creative": {"primary": "#d97706", "secondary": "#7c3aed", "accent": "#fef3c7"}
    }
    
    colors_scheme = template_colors.get(template_type, template_colors["classic"])
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24 if template_type != "creative" else 26,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor(colors_scheme["primary"])
    )
    
    subheader_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor(colors_scheme["secondary"])
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12 if template_type != "creative" else 13,
        leading=16,
        textColor=colors.HexColor(colors_scheme["primary"]),
        spaceBefore=10,
        spaceAfter=6,
    )
    
    content_style = ParagraphStyle(
        'Content',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        textColor=colors.black,
    )
    
    story = []
    
    # Header
    story.append(Paragraph(form_data["name"], header_style))
    
    contact_fields = [form_data["field_of_study"], form_data["email"], form_data["phone"]]
    if form_data["city"] or form_data["country"]:
        contact_fields.append(f"{form_data['city']}, {form_data['country']}")
    contact_lines = [f for f in contact_fields if f]
    if form_data["portfolio"]:
        contact_lines.append(f"GitHub: {form_data['portfolio']}")
    if form_data["website"]:
        contact_lines.append(f"LinkedIn: {form_data['website']}")
    
    contact = "<br/>".join(contact_lines)
    story.append(Paragraph(contact, subheader_style))
    story.append(Spacer(1, 10))
    
    if template_type != "minimal":
        story.append(HRFlowable(width='100%', thickness=0.8, color=colors.HexColor(colors_scheme["accent"])))
    else:
        story.append(HRFlowable(width='100%', thickness=1.0, color=colors.black))
    
    story.append(Spacer(1, 10))
    
    # Professional Summary
    summary_text = enhance_objective(form_data["objective"], form_data["field_of_study"])
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
    story.append(Paragraph(summary_text, content_style))
    story.append(Spacer(1, 10))
    
    # Education
    story.append(Paragraph("EDUCATION", section_style))
    education_text = f"""
    <b>{form_data['school_name']}</b><br/>
    {form_data['degree_type'] or 'Bachelor of Science'} in {form_data['field_of_study']}<br/>
    {form_data['school_location']}<br/>
    {('Expected Graduation: ' + form_data['grad_year']) if form_data['grad_year'] else ''}
    {('<br/>Score: ' + form_data['school_percentage']) if form_data['school_percentage'] else ''}
    """
    story.append(Paragraph(education_text, content_style))
    story.append(Spacer(1, 10))
    
    # Technical Skills
    if form_data["technical_skills"].strip():
        story.append(Paragraph("TECHNICAL SKILLS", section_style))
        skills_list = [skill.strip() for skill in re.split(r'[\n,]+', form_data["technical_skills"]) if skill.strip()]
        skills_text = "<br/>".join(f"• {skill}" for skill in skills_list)
        story.append(Paragraph(skills_text, content_style))
        story.append(Spacer(1, 10))
    
    if form_data["languages"].strip():
        story.append(Paragraph("LANGUAGES", section_style))
        language_list = [lang.strip() for lang in re.split(r'[\n,]+', form_data["languages"]) if lang.strip()]
        story.append(Paragraph("<br/>".join(f"• {lang}" for lang in language_list), content_style))
        story.append(Spacer(1, 10))
    
    # Projects
    project_lines = parse_projects(form_data["projects"])
    if project_lines:
        story.append(Paragraph("PROJECTS", section_style))
        for index, project in enumerate(project_lines, 1):
            project_bullets = describe_project(project)
            project_text = f"<b>{index}. {project}</b><br/>"
            project_text += "<br/>".join(f"• {bullet}" for bullet in project_bullets)
            story.append(Paragraph(project_text, content_style))
            story.append(Spacer(1, 8))
    
    # Internships
    if form_data["internships"].strip():
        story.append(Paragraph("INTERNSHIPS", section_style))
        story.append(Paragraph(form_data["internships"].replace("\\n", "<br/>"), content_style))
        story.append(Spacer(1, 10))
    
    # Certifications
    if form_data["certifications"].strip():
        story.append(Paragraph("CERTIFICATIONS", section_style))
        for cert in form_data["certifications"].split("\\n"):
            cert = cert.strip()
            if cert:
                story.append(Paragraph(f"• {cert}", content_style))
    
    doc.build(story)

# =====================================================================
# RESUME FORM
# =====================================================================
@app.route("/resume-form", methods=["GET", "POST"])
def resume_form():

    uid = session.get("uid")

    if not uid or session.get("role") != "student":
        return redirect("/login")

    db = get_db()

    student = db.execute(
        "SELECT uid, roll, name, department FROM students WHERE uid = ?",
        [uid]
    ).fetchone()

    db.close()

    if not student:
        return "Student profile not found", 404

    if request.method == "POST":

        # Get form data
        pdf_folder = os.path.join(app.static_folder, "resumes")
        os.makedirs(pdf_folder, exist_ok=True)

        pdf_name = f"resume_{uid}_{int(datetime.now().timestamp())}.pdf"
        pdf_path_disk = os.path.join("static", "resumes", pdf_name)
        full_pdf_path = os.path.join(app.root_path, pdf_path_disk)

        # Collect form data
        form_data = {
            "name": clean_text(request.form.get("name", "")),
            "email": clean_text(request.form.get("email", "")),
            "phone": clean_text(request.form.get("phone", "")),
            "city": clean_text(request.form.get("city", "")),
            "country": clean_text(request.form.get("country", "")),
            "objective": request.form.get("objective", ""),
            "technical_skills": clean_text(request.form.get("technical_skills", "")),
            "projects": request.form.get("projects", ""),
            "certifications": request.form.get("certifications", ""),
            "internships": clean_text(request.form.get("internships", "")),
            "school_name": clean_text(request.form.get("school_name", "")),
            "school_location": clean_text(request.form.get("school_location", "")),
            "field_of_study": clean_text(request.form.get("field_of_study", "")),
            "grad_year": clean_text(request.form.get("graduation_year", "")),
            "portfolio": clean_text(request.form.get("portfolio", "")),
            "website": clean_text(request.form.get("website", "")),
            "degree_type": clean_text(request.form.get("degree_type", "")),
            "school_percentage": clean_text(request.form.get("school_percentage", "")),
            "languages": clean_text(request.form.get("languages", "")),
        }

        # Get selected template (default to classic)
        template_type = request.form.get("template", "classic").lower()
        if template_type not in ["classic", "modern", "minimal", "academic", "creative"]:
            template_type = "classic"

        # Generate PDF with selected template
        generate_resume_pdf(template_type, form_data, student, full_pdf_path)

        # Save to database
        student_uid, roll, student_name, dept = student

        conn = get_db()

        conn.execute(
            """
            INSERT INTO resumes
            (student_id, uid, pdf_path, title, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                student_uid,
                uid,
                pdf_path_disk,
                f"{student_name}'s Resume ({template_type.title()})",
                datetime.now()
            ]
        )

        conn.commit()
        conn.close()

        return redirect("/student-dashboard")

    return render_template(
        "resume-form.html",
        student=student
    )

# =====================================================================
# DOWNLOAD 
# =====================================================================

@app.route("/download-resume/<int:resume_id>")
def download_resume(resume_id):
    db = get_db()
    row = db.execute("SELECT pdf_path FROM resumes WHERE id = ?", [resume_id]).fetchone()
    db.close()

    if not row:
        return "Resume not found in database", 404

    pdf_path_in_db = row["pdf_path"] if isinstance(row, sqlite3.Row) else row[0]
    full_path = os.path.join(app.root_path, pdf_path_in_db)

    if not os.path.exists(full_path):
        return f"PDF file not found on disk: {full_path}", 404

    return send_file(full_path, mimetype="application/pdf")

# =====================================================================
# VIEW RESUME
# =====================================================================

@app.route("/view-resume/<int:resume_id>")
def view_resume(resume_id):
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

    pdf_path_in_db = row["pdf_path"] if isinstance(row, sqlite3.Row) else row[0]
    full_path = os.path.join(app.root_path, pdf_path_in_db)

    if not os.path.exists(full_path):
        return f"PDF file not found on disk: {full_path}", 404

    return send_file(full_path, mimetype="application/pdf")
# =====================================================================
#  FACULTY VIEW RESUME
# =====================================================================

@app.route("/faculty/resumes")
def faculty_resumes():
    if session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()

    rows = db.execute("""
        SELECT
            r.id, r.uid, r.title, r.pdf_path, r.created_at,
            s.roll, s.name, s.department
        FROM resumes r
        JOIN students s ON r.uid = s.uid
        ORDER BY s.department, s.roll
    """).fetchall()

    # Convert sqlite3.Row objects to plain dicts for Jinja compatibility
    resumes = [dict(r) for r in rows]

    db.close()

    return render_template("faculty-resumes.html", resumes=resumes, session=session)


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

    row = db.execute(
        "SELECT pdf_path FROM resumes WHERE id = ? AND uid = ?",
        [resume_id, uid]
    ).fetchone()

    if not row:
        db.close()
        return "Resume not found", 404

    pdf_path_in_db = row["pdf_path"] if isinstance(row, sqlite3.Row) else row[0]
    pdf_path_on_disk = os.path.join(app.root_path, pdf_path_in_db)

    if os.path.exists(pdf_path_on_disk):
        os.remove(pdf_path_on_disk)

    db.execute("DELETE FROM resumes WHERE id = ? AND uid = ?", [resume_id, uid])
    db.commit()
    db.close()

    return redirect("/student-dashboard")

# =====================================================================
# STUDENT DETAILS
# =====================================================================

@app.route("/student-details/<int:student_uid>")
def student_details(student_uid):
    if session.get("role") != "faculty":
        return redirect("/login")

    db = get_db()
    db.row_factory = sqlite3.Row
    
    # Get student details with contact information
    student = db.execute(
        """
        SELECT s.uid, s.roll, s.name, s.department, s.cgpa, s.sgpa, s.attendance,
               u.email, u.phone
        FROM students s
        LEFT JOIN users u ON s.uid = u.uid
        WHERE s.uid = ?
        """,
        [student_uid]
    ).fetchone()
    
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

# =====================================================================
# TEST CASE
# =====================================================================
@app.route("/test")
def test():
    return render_template("test.html")


# =====================================================================
#  CHECK AUTH STATUS
# =====================================================================
@app.route("/check-auth")
def check_auth():
    return jsonify({
        "logged_in": "uid" in session,
        "role": session.get("role")
    })


# =====================================================================
#  LOGOUT 
# =====================================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =====================================================================
# CHAT BOX
# =====================================================================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip().lower()
    if not user_msg:
        return jsonify({"reply": "Please type a message."})

    # Enhanced chat responses - Comprehensive knowledge base
    responses = {
        "hello": "Hello! Welcome to the ML Department portal. How can I help you today?",
        "hi": "Hi there! I'm here to assist you with information about our department.",
        "help": "I can assist with:\n• Department programs & details\n• Faculty information & expertise\n• Placement & job offers\n• Study topics (AI, ML, Data Science)\n• Resume templates (5 formats)\n• Pass percentage & attendance\n• Student resources\n• Previous year papers\n• Contact details\n\nWhat would you like to know?",
        "department": "We offer three specialized programs:\n• ACSML: Applied Computer Science and Machine Learning\n• NCSML: Neural Computing and Systems Machine Learning\n• DCSML: Data Science and Computational Machine Learning\n\nEach focuses on AI/ML with 100+ guided projects.",
        "faculty": "Our faculty specializes in:\n• Machine Learning & Deep Learning\n• Data Science & Analytics\n• AI & Computer Vision\n• Natural Language Processing\n• Cybersecurity & Cloud\n\nFaculty regularly publish in top conferences and guide research.",
        "faculty details": "For faculty profiles, visit Faculty section homepage. Each has research areas, publications, and office hours for consultations.",
        "student": "Students can:\n• Build professional resumes (5 templates)\n• Track CGPA, SGPA, attendance\n• View previous year papers\n• Access placement statistics\n• Manage project portfolios\n\nLogin to dashboard for full access.",
        "resume": "Our resume builder offers:\n• 5 professional templates\n• 100+ project descriptions\n• Career objective generator\n• Auto project enhancement\n• One-click PDF download\n\nChoose a template and start building!",
        "templates": "Resume Templates:\n📋 Classic ATS - Corporate/Finance\n✨ Modern Student - Startups\n💼 Minimal Tech - FAANG Tech\n🎓 Academic - Research positions\n🎨 Creative - Design-focused roles",
        "contact": "Reach us:\n• Email: info@ml-dept.edu\n• Phone: +91-9876543210\n• Address: Loyola Academy, Old Alwal, Secunderabad\n• Office Hours: Monday-Friday 9 AM - 5 PM",
        "admission": "Programs:\n• BTech CS (ML specialization)\n• MTech Machine Learning\n• Selection: Merit-based entrance exam\n• Visit our website for applications.",
        "placement": "Placement Stats:\n• 95%+ placement rate\n• Average: 8-12 LPA\n• Top recruiters: Google, Microsoft, Amazon, Goldman Sachs\n• Profiles: ML Engineer, Data Scientist, AI Developer\n• Internships: 4-6 months, 70%+ conversion to full-time",
        "pass percentage": "Department maintains 90%+ pass rate. Requirements:\n• 75%+ attendance for placement eligibility\n• 65%+ minimum for exam appearance\n• Below 65%: Shortage, special permission needed",
        "attendance": "Attendance Policy:\n• 75% minimum for placement eligibility\n• 65% minimum for exam appearance\n• Below 65%: Marked as shortage\n• Tracked for theory and practical courses",
        "job offers": "Offers from:\n• FAANG: Google, Amazon, Facebook, Apple, Netflix\n• Finance: Goldman Sachs, JP Morgan, Citibank\n• Consulting: McKinsey, BCG, EY\n• Startups: Unacademy, Byju's, OYO\n• Average: 8-12 LPA, 12-20 LPA for experienced",
        "internship": "Internships:\n• Duration: 4-6 months\n• Stipend: 30,000-60,000/month\n• Companies: Microsoft, Amazon, Samsung, Infosys\n• Profiles: ML, Data Analyst, Software Dev\n• 70%+ convert to full-time offers",
        "project": "Student projects:\n• ML algorithms & NLP\n• Data analysis & visualization\n• AI chatbots & systems\n• Image recognition & vision\n• Recommendation engines\n• Web apps & APIs\n• Research & publications",
        "machine learning": "Topics covered:\n• Supervised Learning (Regression, Classification)\n• Unsupervised Learning (Clustering, Reduction)\n• Deep Learning (CNNs, RNNs, Transformers)\n• NLP & Text Processing\n• Reinforcement Learning\n• Time Series Forecasting\n• Model Deployment",
        "ai": "AI Fundamentals:\n• Neural Networks & Deep Learning\n• Computer Vision (Image Classification, Detection)\n• NLP (Text Analysis, Chatbots)\n• Knowledge Representation\n• Search & Game Theory\n• Ethical AI & Responsible ML",
        "data science": "Data Science Topics:\n• Statistical Analysis & Testing\n• Data Cleaning & Preprocessing\n• Exploratory Data Analysis (EDA)\n• Predictive Modeling\n• Big Data (Spark, Hadoop)\n• BI & Dashboards\n• A/B Testing",
        "objective": "Career Objective Tips:\n• Highlight key strengths\n• Mention field of interest\n• Specify role type (Internship/Full-time)\n• Include 2-3 year goals\n\nExample: 'ML Engineer seeking to build scalable AI solutions and contribute to cutting-edge research projects.'",
        "career objective": "Strong objective includes:\n1. Your expertise\n2. Passion/interest area\n3. Goal (role/company type)\n4. Value you bring\n\nKeep concise, specific, 2-4 lines.",
        "resume objective": "Tailor to job! Include relevant skills from job description. Make it powerful, specific, under 4 lines.",
        "help objective": "Tell me: What's your main skill? What field? What type of role? I'll suggest a polished version!",
        "help project": "Format: '[Project Name] - [Tech] - [Impact]'\nExample: 'Movie Recommendation - Python, Filtering - 85% accuracy'\nOne per line, I'll enhance!",
        "help projects": "Enter projects with:\n• Project name\n• Technologies\n• Outcome/impact\n\nI'll auto-expand with professional descriptions!",
        "previous year papers": "Previous Year Papers:\n• Login to dashboard\n• Click 'Previous Year Papers' sidebar\n• Available for all semesters\n• All departments covered\n• Use for exam prep & practice",
        "papers": "Click 'Previous Year Papers' in sidebar to download all question papers for exam preparation!",
        "thank": "You're welcome! Ask anytime.",
        "bye": "Goodbye! Have a great day.",
        "goodbye": "Stay connected with our department!",
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
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)