import mysql.connector
from datetime import datetime, time

# SUBJECT SCHEDULE
from datetime import datetime, timedelta

now = datetime.now()

schedule = [
    ("Subject1", now.time(), (now + timedelta(minutes=2)).time()),
    (
        "Subject2",
        (now + timedelta(minutes=2)).time(),
        (now + timedelta(minutes=4)).time(),
    ),
    (
        "Subject3",
        (now + timedelta(minutes=4)).time(),
        (now + timedelta(minutes=6)).time(),
    ),
]

# ------------------ MYSQL CONNECTION ------------------

db = mysql.connector.connect(
    host="localhost",
    user="attendance_user",
    password="1234",
    database="face_attendance",
    auth_plugin="mysql_native_password",
)

cursor = db.cursor()


cursor = db.cursor()

today = datetime.now().date()

# Get logs
cursor.execute(
    """
    SELECT students.id, students.name, logs.login_time, logs.logout_time
    FROM logs
    JOIN students ON logs.student_id = students.id
    WHERE logs.date=%s
""",
    (today,),
)

records = cursor.fetchall()

attendance = {}

for student_id, name, login, logout in records:
    if logout is None:
        continue

    if student_id not in attendance:
        attendance[student_id] = {
            "name": name,
            "subjects": {sub[0]: 0 for sub in schedule},
        }

    for subject, start, end in schedule:
        class_start = datetime.combine(today, start)
        class_end = datetime.combine(today, end)

        overlap_start = max(login, class_start)
        overlap_end = min(logout, class_end)

        if overlap_start < overlap_end:
            minutes = (overlap_end - overlap_start).total_seconds() / 60
            attendance[student_id]["subjects"][subject] += minutes


print("\nSaving Attendance...\n")

# Insert into attendance table
for student_id, data in attendance.items():
    name = data["name"]

    for subject, minutes in data["subjects"].items():
        status = "Present" if minutes >= 30 else "Absent"

        cursor.execute(
            """
            INSERT INTO attendance
            (student_id, subject, date, minutes_present, status)
            VALUES (%s,%s,%s,%s,%s)
        """,
            (student_id, subject, today, round(minutes, 1), status),
        )

        print(f"{name} - {subject}: {round(minutes, 1)} min → {status}")

db.commit()

print("\nAttendance Stored Successfully ✅")
