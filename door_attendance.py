import cv2
import face_recognition
import pickle
import mysql.connector
from datetime import datetime

# ------------------ MYSQL CONNECTION ------------------

db = mysql.connector.connect(
    host="localhost",
    user="attendance_user",
    password="1234",
    database="face_attendance",
    auth_plugin="mysql_native_password",
)

cursor = db.cursor()

# ------------------ LOAD ENCODINGS ------------------

with open("encodings.pkl", "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]

# ------------------ STATUS TRACKING ------------------

inside_status = {}  # name: True/False
session_start = {}  # name: datetime
total_time = {}  # name: total seconds
last_action = {}  # name: datetime

COOLDOWN = 5  # seconds (prevents fast toggle)
ATTENDANCE_LIMIT = 15  # 15 sec demo (change to 1800 for 30 min)

# ------------------ CAMERA ------------------

cap = cv2.VideoCapture(0)

print("Door Attendance System Started")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb)
    face_encodings = face_recognition.face_encodings(rgb, face_locations)

    for (top, right, bottom, left), face_encoding in zip(
        face_locations, face_encodings
    ):
        matches = face_recognition.compare_faces(
            known_encodings, face_encoding, tolerance=0.5
        )

        name = "Unknown"

        if True in matches:
            index = matches.index(True)
            name = known_names[index]

            # -------- STUDENT CHECK --------
            cursor.execute("SELECT id FROM students WHERE name=%s", (name,))
            result = cursor.fetchone()

            if not result:
                cursor.execute("INSERT INTO students (name) VALUES (%s)", (name,))
                db.commit()
                student_id = cursor.lastrowid
            else:
                student_id = result[0]

            now = datetime.now()
            today = now.date()

            # -------- COOLDOWN CHECK --------
            if name in last_action:
                diff = (now - last_action[name]).total_seconds()
                if diff < COOLDOWN:
                    continue

            # ---------------- LOGIN ----------------
            if not inside_status.get(name, False):
                cursor.execute(
                    "INSERT INTO logs (student_id, login_time, date) VALUES (%s,%s,%s)",
                    (student_id, now, today),
                )
                db.commit()

                session_start[name] = now
                inside_status[name] = True
                last_action[name] = now

                print(f"{name} LOGGED IN at {now}")

            # ---------------- LOGOUT ----------------
            else:
                cursor.execute(
                    "SELECT id, login_time FROM logs WHERE student_id=%s AND logout_time IS NULL ORDER BY id DESC LIMIT 1",
                    (student_id,),
                )
                log_data = cursor.fetchone()

                if log_data:
                    log_id = log_data[0]
                    login_time = log_data[1]

                    duration = (now - login_time).total_seconds()

                    # Accumulate total time
                    total_time[name] = total_time.get(name, 0) + duration

                    cursor.execute(
                        "UPDATE logs SET logout_time=%s WHERE id=%s",
                        (now, log_id),
                    )
                    db.commit()

                    print(f"{name} LOGGED OUT")
                    print(f"Session Duration: {duration:.2f} sec")
                    print(f"Total Time: {total_time[name]:.2f} sec")

                    # -------- Attendance Condition --------
                    if total_time[name] >= ATTENDANCE_LIMIT:
                        print(f"{name} Attendance Marked ✅")

                inside_status[name] = False
                last_action[name] = now

        # -------- DRAW FACE BOX --------
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(
            frame,
            name,
            (left, top - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

    cv2.imshow("Door Attendance", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
