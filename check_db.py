import sqlite3

conn = sqlite3.connect('database/ml_dept.db')
cursor = conn.cursor()

# Get users without students
users_without_students = cursor.execute("""
    SELECT u.uid, u.username, u.name, u.role 
    FROM users u 
    LEFT JOIN students s ON u.uid = s.uid 
    WHERE s.uid IS NULL
""").fetchall()

print("Users without student records:")
for row in users_without_students:
    print(f"  UID: {row[0]}, Username: {row[1]}, Name: {row[2]}, Role: {row[3]}")

print("\n\nAll users:")
all_users = cursor.execute("SELECT uid, username, name, role FROM users").fetchall()
for row in all_users:
    print(f"  UID: {row[0]}, Username: {row[1]}, Name: {row[2]}, Role: {row[3]}")

conn.close()
