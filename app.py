from flask import Flask, send_file, render_template, request, redirect, session, current_app, jsonify
import sqlite3
import hashlib
import os
import re
from flask import url_for
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    FrameBreak,
    Image,
    KeepTogether,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfform
from reportlab.lib.units import mm




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
    # Clean and escape for ReportLab Paragraphs
    text = str(text).strip()
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", "<br/>")
    for wrong, right in COMMON_SPELLING_FIXES.items():
        text = re.sub(rf"\b{wrong}\b", right, text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text


def enhance_objective(objective, field_of_study):
    objective = clean_text(objective)
    if not objective:
        field = field_of_study or "Machine Learning"
        return f"Results-oriented {field} professional with a focus on delivering high-impact technical solutions through advanced machine learning methodologies and scalable software architecture."
    if len(objective.split()) < 15:
        objective = objective.rstrip('.')
        objective += ", eager to contribute to innovative teams and dedicated to leveraging data-driven insights to solve complex challenges."
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
        bullets.append("Architected a sophisticated recommendation system utilizing collaborative filtering and matrix factorization to enhance user engagement.")
        bullets.append("Optimized model performance to achieve 85%+ predictive accuracy across diverse user datasets.")
        bullets.append("Engineered real-time prediction pipelines for seamless integration into production environments.")
    elif any(word in lower for word in ["sentiment", "emotion", "opinion"]):
        bullets.append("Built NLP pipeline for sentiment analysis with text preprocessing.")
        bullets.append("Trained classifiers with 90%+ accuracy on labeled datasets.")
        bullets.append("Deployed model for real-time social media monitoring.")
        bullets.append("Developed an advanced NLP pipeline for multi-class sentiment analysis, incorporating custom text preprocessing and tokenization.")
        bullets.append("Spearheaded the training of neural classifiers, attaining 90%+ accuracy on large-scale labeled datasets.")
        bullets.append("Leveraged automated monitoring tools to deploy the model for real-time opinion mining and trend analysis.")
    elif any(word in lower for word in ["image", "vision", "cnn", "object detection"]):
        bullets.append("Designed CNN architecture using TensorFlow/PyTorch.")
        bullets.append("Applied data augmentation and transfer learning techniques.")
        bullets.append("Achieved 92%+ accuracy on image classification benchmarks.")
        bullets.append("Engineered deep learning architectures using CNNs and Transfer Learning to solve complex computer vision challenges.")
        bullets.append("Optimized training efficiency by implementing data augmentation and automated hyperparameter tuning.")
        bullets.append("Surpassed industry benchmarks with a 92%+ accuracy rate on competitive image classification tasks.")
    elif any(word in lower for word in ["chatbot", "conversational", "nlp"]):
        bullets.append("Built NLP pipeline for intent recognition and response generation.")
        bullets.append("Integrated with Flask backend for multi-turn dialogue capability.")
        bullets.append("Deployed with context awareness and 95%+ user satisfaction.")
        bullets.append("Orchestrated the development of a context-aware conversational AI utilizing state-of-the-art NLP techniques for intent recognition.")
        bullets.append("Streamlined multi-turn dialogue flows through robust backend integration with Flask and RESTful APIs.")
        bullets.append("Achieved a 95%+ user satisfaction rating by focusing on response latency and conversational accuracy.")
    elif any(word in lower for word in ["forecasting", "prediction", "time series"]):
        bullets.append("Applied ARIMA and Prophet models for time-series forecasting.")
        bullets.append("Achieved RMSE of 5-8% on validation datasets.")
        bullets.append("Built interactive dashboards for trend visualization and insights.")
        bullets.append("Leveraged ARIMA and Prophet models to deliver high-precision time-series forecasting for critical business metrics.")
        bullets.append("Minimized forecasting error, achieving a significantly low RMSE of 5-8% across validation cycles.")
        bullets.append("Designed interactive visualization dashboards to translate complex data trends into actionable strategic insights.")
    elif any(word in lower for word in ["clustering", "segmentation"]):
        bullets.append("Implemented K-means, DBSCAN, and hierarchical clustering.")
        bullets.append("Optimized using silhouette analysis and elbow method.")
        bullets.append("Discovered actionable customer segments improving ROI by 25%.")
        bullets.append("Implemented unsupervised learning algorithms, including K-means and DBSCAN, to uncover hidden patterns in large datasets.")
        bullets.append("Refined clustering accuracy through rigorous silhouette analysis and optimized feature engineering.")
        bullets.append("Identified high-value customer segments, directly contributing to a 25% projected improvement in targeted marketing ROI.")
    elif any(word in lower for word in ["web", "flask", "django", "frontend", "backend"]):
        bullets.append("Built full-stack web application with responsive UI and scalable backend.")
        bullets.append("Implemented authentication, database management, and REST APIs.")
        bullets.append("Deployed with Docker and integrated GitHub CI/CD pipeline.")
        bullets.append("Spearheaded the design and deployment of a full-stack web application featuring a responsive UI and scalable backend infrastructure.")
        bullets.append("Integrated secure authentication protocols, efficient database management, and high-performance REST APIs.")
        bullets.append("Automated the deployment lifecycle using Docker containers and robust CI/CD pipelines.")
    elif any(word in lower for word in ["machine learning", "ml", "deep learning", "neural"]):
        bullets.append("Designed and trained ML models for real-world problem solving.")
        bullets.append("Implemented data preprocessing, feature engineering, and model evaluation.")
        bullets.append("Optimized hyperparameters achieving 88%+ accuracy on test data.")
        bullets.append("Developed end-to-end machine learning solutions to address real-world business challenges and operational bottlenecks.")
        bullets.append("Executed comprehensive data preprocessing, advanced feature engineering, and rigorous model evaluation frameworks.")
        bullets.append("Optimized model reliability and performance, consistently achieving 88%+ accuracy on unseen test data.")
    elif any(word in lower for word in ["automation", "script", "tool", "pipeline"]):
        bullets.append("Automated critical workflows improving productivity by 40%+.")
        bullets.append("Developed robust scripts with error handling and monitoring.")
        bullets.append("Documented thoroughly for easy maintenance and scalability.")
        bullets.append("Pioneered workflow automation initiatives, resulting in a documented 40%+ increase in operational productivity.")
        bullets.append("Developed robust, fault-tolerant scripts with integrated error handling and performance monitoring.")
        bullets.append("Produced comprehensive technical documentation to ensure long-term scalability and ease of maintenance.")
    else:
        bullets.append("Developed a practical solution with focus on usability and performance.")
        bullets.append("Implemented core features using industry best practices and design patterns.")
        bullets.append("Tested rigorously and optimized for production deployment.")
        bullets.append("Engineered a practical, performance-driven solution tailored to specific user needs and industry standards.")
        bullets.append("Leveraged industry best practices and modern design patterns to implement core functional modules.")
        bullets.append("Conducted rigorous stress testing and optimization to ensure stability in production environments.")

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
    
    # Detect if request is from AJAX script.js
    is_ajax = request.is_json
    if is_ajax:
        data = request.get_json()
        uid = data.get("uid") or data.get("username")
        password = data.get("password")
        role = data.get("role") or data.get("mode")

    if not all([uid, password, role]):
        if is_ajax: return jsonify({"success": False, "message": "Missing fields"})
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
        if is_ajax: return jsonify({"success": False, "message": "Invalid UID or User not found"})
        return render_template("login.html", error="Invalid UID - No such user found")

    db_uid = row["uid"]
    username = row["username"]
    db_hash = row["password_hash"]
    db_role = row["role"]
    full_name = row["name"]
    email = row["email"]
    phone = row["phone"]

    if db_hash != h:
        if is_ajax: return jsonify({"success": False, "message": "Invalid password"})
        return render_template("login.html", error="Invalid password")

    if db_role != role:
        if is_ajax: return jsonify({"success": False, "message": "Role mismatch"})
        return render_template("login.html", error="Role mismatch")

    session["uid"] = db_uid
    session["username"] = username
    session["role"] = db_role
    session["name"] = full_name

    if is_ajax:
        return jsonify({"success": True, "message": "Login successful!", "role": db_role})

    if db_role == "student":
        return redirect(url_for("student_dashboard"))
    else:
        return redirect(url_for("faculty_dashboard"))


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
        return redirect(url_for("login"))

    if session.get("role") != "student":
        return redirect(url_for("login"))

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

@app.route("/resume-form")
def resume_form():
    if "uid" not in session:
        return redirect(url_for("login"))
    return render_template("form.html", session=session)

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
        return redirect(url_for("login"))

    db = get_db()
    students = db.execute(
        """
        SELECT s.*, u.email, u.phone 
        FROM students s 
        JOIN users u ON s.uid = u.uid 
        WHERE s.department = ? 
        ORDER BY s.roll
        """,
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
            return redirect(url_for("login"))

        dept = request.args.get("dept", None)  # from URL: ?dept=ACSML

        db = get_db()

        def get_students_for(department):
            if dept is None or dept == department:
                return db.execute(
                    """
                    SELECT s.*, u.email, u.phone
                    FROM students s
                    JOIN users u ON s.uid = u.uid
                    WHERE s.department = ?
                    ORDER BY s.roll
                    """,
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
        return redirect(url_for("login"))

    db = get_db()

    if request.method == "GET":
        student = db.execute(
            """
            SELECT s.uid, s.roll, s.name, s.department, s.cgpa, s.sgpa, s.attendance,
                   u.email, u.phone
            FROM students s
            JOIN users u ON s.uid = u.uid
            WHERE s.uid = ?
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
    email = request.form.get("email")
    phone = request.form.get("phone")
    cgpa = float(request.form.get("cgpa", 0.0) or 0.0)
    sgpa = float(request.form.get("sgpa", 0.0) or 0.0)
    attendance = int(request.form.get("attendance", 0) or 0)
    

    if not all([department, roll, name]):
        db.close()
        return "Missing required fields", 400

    try:
        # Update users table to keep name, email and phone in sync
        db.execute(
            """
            UPDATE users
            SET name = ?, email = ?, phone = ?
            WHERE uid = ?
            """,
            [name, email, phone, uid]
        )

        # Update students table
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

    return redirect(url_for("faculty_dashboard"))


# =====================================================================
# FACULTY ADD STUDENT PAGE
# =====================================================================
@app.route("/faculty/add-student", methods=["GET"])
def faculty_add_student_form():

    if session.get("role") != "faculty":
        return redirect(url_for("login"))

    return render_template("faculty-add-student.html")


# =====================================================================
# FACULTY ADD STUDENT SAVE
# =====================================================================
@app.route("/faculty/add-student", methods=["POST"])
def faculty_add_student():

    if session.get("role") != "faculty":
        return redirect(url_for("login"))

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

    return redirect(url_for("faculty_dashboard"))
# =====================================================================
# FACULTY DELETE STUDENT SAVE
# =====================================================================

@app.route("/faculty/delete-student/<string:roll>", methods=["POST"])
def faculty_delete_student(roll):

    if session.get("role") != "faculty":
        return redirect(url_for("login"))

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

    return redirect(url_for("faculty_dashboard"))

# =====================================================================
# RESUME TEMPLATE GENERATORS (5 Styles)
# =====================================================================
def split_items(text):
    if not text:
        return []
    return [i.strip() for i in re.split(r'[\n,;]+', text) if i.strip()]
def make_styles(template_type):
    styles = getSampleStyleSheet()
    body_font = "Times-Roman" if template_type == "academic" else "Helvetica"
    bold_font = "Times-Bold" if template_type == "academic" else "Helvetica-Bold"

    palette = {
        "classic": ("#111827", "#4b5563", "#d1d5db"),
        "modern": ("#0f172a", "#475569", "#cbd5e1"),
        "minimal": ("#111111", "#52525b", "#e5e7eb"),
        "academic": ("#1b3399", "#475569", "#bfd0ff"),
        "creative": ("#7c3aed", "#6b7280", "#ddd6fe"),
    }
    primary, muted, line = palette.get(template_type, palette["classic"])
    primary = colors.HexColor(primary)
    muted = colors.HexColor(muted)
    line = colors.HexColor(line)

    return {
        "title": ParagraphStyle("title", parent=styles["Normal"], fontName=bold_font, fontSize=23, leading=27, textColor=primary, alignment=TA_LEFT, spaceAfter=3),
        "subtitle": ParagraphStyle("subtitle", parent=styles["Normal"], fontName=body_font, fontSize=10.2, leading=13, textColor=muted, spaceAfter=7),
        "section": ParagraphStyle("section", parent=styles["Heading2"], fontName=bold_font, fontSize=11.2, leading=14, textColor=primary, spaceBefore=6, spaceAfter=5),
        "body": ParagraphStyle("body", parent=styles["BodyText"], fontName=body_font, fontSize=9.3, leading=12.6, textColor=colors.black),
        "small": ParagraphStyle("small", parent=styles["BodyText"], fontName=body_font, fontSize=8.6, leading=11, textColor=muted),
        "center_title": ParagraphStyle("center_title", parent=styles["Normal"], fontName=bold_font, fontSize=24, leading=28, textColor=primary, alignment=TA_CENTER, spaceAfter=2),
        "center_sub": ParagraphStyle("center_sub", parent=styles["Normal"], fontName=body_font, fontSize=10, leading=12, textColor=muted, alignment=TA_CENTER),
        "right_small": ParagraphStyle("right_small", parent=styles["Normal"], fontName=body_font, fontSize=8.7, leading=11, textColor=muted, alignment=TA_RIGHT),
        "line": line,
        "primary": primary,
        "muted": muted,
    }

def header_band(canvas, doc, form_data, template_type):
    canvas.saveState()
    w, h = A4
    name = clean_text(form_data.get("name"))

    if template_type == "modern":
        canvas.setFillColor(colors.HexColor("#0f172a"))
        canvas.rect(0, h - 52, w, 52, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawString(18 * mm, h - 28, name)
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(w - 18 * mm, h - 28, clean_text(form_data.get("field_of_study")))

    elif template_type == "academic":
        canvas.setStrokeColor(colors.HexColor("#1b3399"))
        canvas.setLineWidth(1.4)
        canvas.line(doc.leftMargin, h - 22, w - doc.rightMargin, h - 22)
        canvas.setFont("Times-Bold", 16)
        canvas.setFillColor(colors.HexColor("#1b3399"))
        canvas.drawCentredString(w / 2, h - 15, name)

    elif template_type == "creative":
        canvas.setFillColor(colors.HexColor("#7c3aed"))
        canvas.rect(0, h - 60, w, 60, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawString(18 * mm, h - 31, name)
        canvas.setFont("Helvetica", 9.5)
        canvas.drawString(18 * mm, h - 44, clean_text(form_data.get("field_of_study")))

    elif template_type == "minimal":
        canvas.setStrokeColor(colors.HexColor("#111111"))
        canvas.line(25 * mm, h - 24, w - 25 * mm, h - 24)

    else:
        canvas.setStrokeColor(colors.HexColor("#d1d5db"))
        canvas.line(doc.leftMargin, h - 26, w - doc.rightMargin, h - 26)
    canvas.restoreState()

def section_box(title, text, styles, fill=None, width=1):
    text = text.replace('\n', '<br/>')
    data = [[Paragraph(f"<b>{title}</b>", styles["body"])], [Paragraph(text, styles["small"])]]
    t = Table(data, colWidths=[None])
    ts = [
        ("BOX", (0, 0), (-1, -1), width, styles["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if fill:
        ts.append(("BACKGROUND", (0, 0), (-1, -1), fill))
    t.setStyle(TableStyle(ts))
    return t

def build_story_common(form_data, styles):
    story = []
    story.append(Paragraph("PROFESSIONAL SUMMARY", styles["section"]))
    story.append(Paragraph(enhance_objective(form_data.get("objective"), form_data.get("field_of_study")), styles["body"]))
    story.append(Spacer(1, 5))

    story.append(Paragraph("EDUCATION", styles["section"]))
    edu = f"<b>{clean_text(form_data.get('school_name'))}</b><br/>{clean_text(form_data.get('degree_type'))} in {clean_text(form_data.get('field_of_study'))}<br/>{clean_text(form_data.get('school_location'))}<br/>Graduation Year: {clean_text(form_data.get('grad_year'))}"
    if form_data.get("school_percentage"):
        edu += f"<br/>Score: {clean_text(form_data.get('school_percentage'))}"
    story.append(Paragraph(edu, styles["body"]))
    story.append(Spacer(1, 5))
    return story

def generate_resume_pdf(template_type, form_data, full_pdf_path):
    template_type = (template_type or "classic").lower()
    if template_type not in ["classic", "modern", "minimal", "academic", "creative"]:
        template_type = "classic"

    styles = make_styles(template_type)

    def on_page(canvas, doc):
        header_band(canvas, doc, form_data, template_type)
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawRightString(A4[0] - doc.rightMargin, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    if template_type == "modern":
        doc = BaseDocTemplate(
            full_pdf_path, pagesize=A4,
            leftMargin=12*mm, rightMargin=12*mm, topMargin=58*mm, bottomMargin=15*mm
        )
        sidebar_w = 60 * mm
        gap = 6 * mm
        main_w = A4[0] - doc.leftMargin - doc.rightMargin - sidebar_w - gap
        frame_h = A4[1] - doc.topMargin - doc.bottomMargin

        left_frame = Frame(doc.leftMargin, doc.bottomMargin, sidebar_w, frame_h, id="sidebar", showBoundary=0)
        right_frame = Frame(doc.leftMargin + sidebar_w + gap, doc.bottomMargin, main_w, frame_h, id="main", showBoundary=0)
        doc.addPageTemplates([PageTemplate(id="modern", frames=[left_frame, right_frame], onPage=on_page)])

        story = []
        # Sidebar Content
        if form_data.get('photo_path') and os.path.exists(form_data['photo_path']):
            try:
                img = Image(form_data['photo_path'], width=38*mm, height=38*mm)
                story.append(img)
                story.append(Spacer(1, 12))
            except:
                pass

        story.append(Paragraph(f"<b>{clean_text(form_data.get('name'))}</b>", styles["title"]))
        story.append(Paragraph(clean_text(form_data.get("field_of_study") or "Professional"), styles["subtitle"]))
        
        story.append(Paragraph("PROFILE", styles["section"]))
        story.append(Paragraph(enhance_objective(form_data.get("objective"), form_data.get("field_of_study")), styles["body"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph("CONTACT", styles["section"]))
        story.append(Paragraph(
            "<br/>".join([
                f"Email: {clean_text(form_data.get('email'))}",
                f"Phone: {clean_text(form_data.get('phone'))}",
                f"Location: {clean_text(form_data.get('city'))}, {clean_text(form_data.get('country'))}",
            ]),
            styles["small"]
        ))
        story.append(Spacer(1, 4))
        story.append(Paragraph("SKILLS", styles["section"]))
        skills = "<br/>".join(f"• {clean_text(x)}" for x in split_items(form_data.get("technical_skills")))
        story.append(Paragraph(skills or "N/A", styles["small"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph("LANGUAGES", styles["section"]))
        langs = "<br/>".join(f"• {clean_text(x)}" for x in split_items(form_data.get("languages")))
        story.append(Paragraph(langs or "N/A", styles["small"]))

        story.append(FrameBreak())
        story.extend(build_story_common(form_data, styles))

        projects = parse_projects(form_data.get("projects"))
        if projects:
            story.append(Paragraph("PROJECTS", styles["section"]))
            for p in projects:
                bullets = describe_project(p)
                txt = f"<b>{clean_text(p)}</b><br/>" + "<br/>".join(f"• {clean_text(b)}" for b in bullets)
                story.append(Paragraph(txt, styles["body"]))
                story.append(Spacer(1, 6))

        if form_data.get("internships"):
            story.append(Paragraph("INTERNSHIPS", styles["section"]))
            story.append(Paragraph(clean_text(form_data.get("internships")), styles["body"]))

        if form_data.get("certifications"):
            story.append(Paragraph("CERTIFICATIONS", styles["section"]))
            story.append(Paragraph("<br/>".join(f"• {clean_text(x)}" for x in split_items(form_data.get("certifications"))), styles["body"]))

        doc.build(story)
        return

    doc = BaseDocTemplate(
        full_pdf_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm, topMargin=26*mm, bottomMargin=15*mm
    )
    story = []

    # Classic layout photo
    if template_type in ["classic", "creative"] and form_data.get('photo_path'):
        try:
            img = Image(form_data['photo_path'], width=30*mm, height=30*mm)
            story.append(img)
            story.append(Spacer(1, 10))
        except:
            pass

    # Minimal layout photo support
    if template_type == "minimal" and form_data.get('photo_path'):
        try:
            img = Image(form_data['photo_path'], width=25*mm, height=25*mm)
            story.append(img)
            story.append(Spacer(1, 5))
        except:
            pass

    if template_type == "classic":
        story.append(Paragraph(clean_text(form_data.get("name")), styles["title"]))
        contact_line = f"{clean_text(form_data.get('field_of_study'))} | {clean_text(form_data.get('email'))} | {clean_text(form_data.get('phone'))}"
        if form_data.get("city"):
            contact_line += f" | {clean_text(form_data.get('city'))}"
        story.append(Paragraph(contact_line, styles["subtitle"]))
        story.append(HRFlowable(width="100%", thickness=0.8, color=styles["line"]))
        story.append(Spacer(1, 5))

    elif template_type == "minimal":
        story.append(Paragraph(clean_text(form_data.get("name")), styles["center_title"]))
        story.append(Paragraph(clean_text(form_data.get("field_of_study")), styles["center_sub"]))
        story.append(Spacer(1, 5))
        story.append(HRFlowable(width="42%", thickness=1, color=styles["line"]))
        story.append(Spacer(1, 7))

    elif template_type == "academic":
        story.append(Paragraph(clean_text(form_data.get("name")), styles["center_title"]))
        story.append(Paragraph("Academic Resume", styles["center_sub"]))
        story.append(Spacer(1, 5))
        story.append(HRFlowable(width="100%", thickness=1, color=styles["line"]))
        story.append(Spacer(1, 7))

    elif template_type == "creative":
        story.append(Paragraph(f"<font color='#7c3aed'><b>{clean_text(form_data.get('name'))}</b></font>", styles["title"]))
        story.append(Paragraph(clean_text(form_data.get("field_of_study")), styles["subtitle"]))
        story.append(HRFlowable(width="100%", thickness=1.2, color=styles["line"]))
        story.append(Spacer(1, 7))

    story.extend(build_story_common(form_data, styles))

    if form_data.get("technical_skills"):
        if template_type == "creative":
            story.append(section_box("TECHNICAL SKILLS", " • ".join(clean_text(x) for x in split_items(form_data.get("technical_skills"))), styles, fill=colors.HexColor("#f5f3ff")))
            story.append(Spacer(1, 5))
        else:
            story.append(Paragraph("TECHNICAL SKILLS", styles["section"]))
            story.append(Paragraph(" • ".join(clean_text(x) for x in split_items(form_data.get("technical_skills"))), styles["body"]))
            story.append(Spacer(1, 5))

    if form_data.get("languages"):
        story.append(Paragraph("LANGUAGES", styles["section"]))
        if template_type == "minimal":
            data = [[Paragraph("Languages", styles["body"]), Paragraph(" • ".join(clean_text(x) for x in split_items(form_data.get("languages"))), styles["small"])]]
            t = Table(data, colWidths=[35*mm, None])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.8, styles["line"]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(t)
        else:
            story.append(Paragraph(" • ".join(clean_text(x) for x in split_items(form_data.get("languages"))), styles["body"]))
        story.append(Spacer(1, 5))

    projects = parse_projects(form_data.get("projects"))
    if projects:    
        story.append(Paragraph("PROJECTS", styles["section"]))
        for i, p in enumerate(projects, 1):
            bullets = describe_project(p)
            txt = f"<b>{clean_text(p)}</b><br/>" + "<br/>".join(f"• {clean_text(b)}" for b in bullets)
            if template_type in ["modern", "creative"]:
                story.append(section_box(f"Project {i}", txt, styles, fill=colors.HexColor("#eff6ff") if template_type == "modern" else colors.HexColor("#faf5ff")))
            else:
                story.append(Paragraph(txt, styles["body"]))
            story.append(Spacer(1, 4))
    if form_data.get("internships"):
        story.append(Paragraph("INTERNSHIPS", styles["section"]))
        story.append(Paragraph(clean_text(form_data.get("internships")), styles["body"]))
        story.append(Spacer(1, 5))
    if form_data.get("certifications"):
        story.append(Paragraph("CERTIFICATIONS", styles["section"]))
        certs = "<br/>".join(f"• {clean_text(x)}" for x in split_items(form_data.get("certifications")))
        story.append(Paragraph(certs, styles["body"]))

    doc.addPageTemplates([
        PageTemplate(
            id=template_type, 
            frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")], 
            onPage=on_page)
    ])
    doc.build(story)

@app.route("/generate", methods=["POST"])
def generate():
    form_data = request.form.to_dict(flat=True)
    template_choice = form_data.get("template", "classic")
    out_dir = "output"
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{clean_text(form_data.get('name') or 'resume').replace(' ', '_')}_{template_choice}.pdf"
    
    # Handle optional profile photo
    photo = request.files.get("profile_photo")
    if photo and photo.filename:
        photo_path = os.path.join(out_dir, f"temp_photo_{session.get('uid', 'anon')}.png")
        photo.save(photo_path)
        form_data['photo_path'] = photo_path

    full_pdf_path = os.path.join(out_dir, filename)
    generate_resume_pdf(template_choice, form_data, full_pdf_path)
    return send_file(full_pdf_path, as_attachment=True, download_name=filename, mimetype="application/pdf")


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
        return redirect(url_for("login"))

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
        return redirect(url_for("login"))

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

    return redirect(url_for("student_dashboard"))

# =====================================================================
# STUDENT DETAILS
# =====================================================================

@app.route("/student-details/<int:student_uid>")
def student_details(student_uid):
    if session.get("role") != "faculty":
        return redirect(url_for("login"))

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
    return redirect(url_for("login"))


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