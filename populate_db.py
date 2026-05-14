import sqlite3
import hashlib
import random
from datetime import datetime

# Connect to database
conn = sqlite3.connect('database/ml_dept.db')
cursor = conn.cursor()

# Sample data for names, departments, etc.
first_names = ['Aarav', 'Vihaan', 'Arjun', 'Reyansh', 'Vivaan', 'Advik', 'Arnav', 'Atharv', 'Ananya', 'Aadhya',
               'Anika', 'Saisha', 'Pari', 'Aaradhya', 'Anvi', 'Navya', 'Diya', 'Sara', 'Riya', 'Maya',
               'Ishaan', 'Kabir', 'Arjun', 'Rohan', 'Aryan', 'Dev', 'Veer', 'Rudra', 'Shiv', 'Kartik',
               'Priya', 'Sneha', 'Kavya', 'Aisha', 'Meera', 'Tara', 'Nisha', 'Pooja', 'Ritu', 'Kiran']

last_names = ['Sharma', 'Verma', 'Gupta', 'Singh', 'Kumar', 'Patel', 'Reddy', 'Rao', 'Naidu', 'Chowdhury',
              'Banerjee', 'Das', 'Saha', 'Ghosh', 'Roy', 'Mukherjee', 'Chatterjee', 'Sen', 'Dutta', 'Mitra']

departments = ['ACSML', 'NCSML', 'DCSML']
roles = ['student', 'faculty']

# Hash for password "123456"
password_hash = hashlib.sha256("123456".encode()).hexdigest()

# Clear existing data
cursor.execute("DELETE FROM users")
cursor.execute("DELETE FROM students")
cursor.execute("DELETE FROM resumes")

# Generate 100 students and 20 faculty (120 total users)
user_id = 1
student_count = 0
faculty_count = 0

for i in range(120):
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    full_name = f"{first_name} {last_name}"

    if i < 100:  # First 100 are students
        role = 'student'
        username = f"student_{user_id}"
        email = f"student{user_id}@example.com"
        department = random.choice(departments)
        roll = f"111726049{str(user_id).zfill(3)}"
        cgpa = round(random.uniform(6.0, 9.5), 1)
        sgpa = round(random.uniform(6.0, 9.8), 1)
        attendance = random.randint(70, 100)

        # Insert user
        cursor.execute("""
            INSERT INTO users (uid, username, password_hash, name, role, email, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, password_hash, full_name, role, email, f"987654{str(user_id).zfill(4)}"))

        # Insert student
        cursor.execute("""
            INSERT INTO students (uid, department, roll, name, cgpa, sgpa, attendance, email, phone, address, date_of_birth)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, department, roll, full_name, cgpa, sgpa, attendance,
              f"{first_name.lower()}.{last_name.lower()}@student.example.com",
              f"987654{str(user_id).zfill(4)}",
              f"Address {user_id}, Hyderabad, Telangana",
              f"2000-{random.randint(1,12):02d}-{random.randint(1,28):02d}"))

        student_count += 1

    else:  # Last 20 are faculty
        role = 'faculty'
        username = f"faculty_{user_id-100}"
        email = f"faculty{user_id-100}@example.com"
        department = random.choice(departments)

        # Insert user
        cursor.execute("""
            INSERT INTO users (uid, username, password_hash, name, role, email, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, password_hash, f"Dr. {full_name}", role, email, f"987655{str(user_id-100).zfill(4)}"))

        faculty_count += 1

    user_id += 1

# Generate some sample resumes for students
resume_titles = ['Software Developer Resume', 'Data Scientist Resume', 'ML Engineer Resume', 'Web Developer Resume', 'AI Specialist Resume']

for student_uid in range(1, 21):  # Create resumes for first 20 students
    for i in range(random.randint(1, 3)):  # 1-3 resumes per student
        title = random.choice(resume_titles)
        pdf_path = f"resumes/resume_{student_uid}_{i+1}.pdf"
        cursor.execute("""
            INSERT INTO resumes (student_id, uid, pdf_path, title, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (student_uid, student_uid, pdf_path, title, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

conn.commit()
conn.close()

print(f"Generated {student_count} students and {faculty_count} faculty members")
print("Database populated with sample data!")