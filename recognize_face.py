import cv2
import face_recognition
import pickle
import mysql.connector
from datetime import datetime
import time

# ================= MYSQL =================

db = mysql.connector.connect(
    host="localhost",
    user="attendance_user",
    password="1234",
    database="face_attendance",
    auth_plugin="mysql_native_password",
)

cursor = db.cursor()

# ================= LOAD FACE DATA =================

with open("encodings.pkl", "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]

# ==================================================
# DEMO SETTINGS
# 4 classes
# each class = 2 min (120 sec)
# need 1 min 30 sec (90 sec) total stay
# multiple entry exit supported
# ==================================================

subjects = ["CS1404", "CS1403", "CS1402", "CS1405"]

CLASS_DURATION = 120  # 2 min
MIN_STAY = 90  # 1 min 30 sec required
COOLDOWN = 3  # anti repeat scan
EXIT_LOCK = 8  # minimum seconds before exit scan

# ================= MEMORY =================

inside = {}
entry_time = {}
last_scan = {}

# total stay per subject per student
stay_memory = {}

# already marked attendance
marked = {}

# school starts once
global_start = time.time()

# ================= CAMERA =================

cap = cv2.VideoCapture(0)

print("Door Attendance Demo Started")
print("Class Duration = 2 min")
print("Need 1 min 30 sec for attendance")
print("1st scan = ENTRY")
print("2nd scan = EXIT")
print("Multiple exits/entries supported")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    now_ts = time.time()
    now = datetime.now()
    today = now.date()

    # current class
    elapsed = int(now_ts - global_start)
    idx_now = elapsed // CLASS_DURATION

    current_subject = subjects[idx_now] if idx_now < len(subjects) else "NO CLASS"

    # ================= FACE DETECT =================

    small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, locations)

    for face_encoding in encodings:
        matches = face_recognition.compare_faces(
            known_encodings, face_encoding, tolerance=0.5
        )

        if True in matches:
            idx = matches.index(True)
            name = known_names[idx]

            # init memory
            if name not in stay_memory:
                stay_memory[name] = {}

            if name not in marked:
                marked[name] = {}

            # cooldown
            if name in last_scan:
                diff = (now - last_scan[name]).total_seconds()
                if diff < COOLDOWN:
                    continue

            last_scan[name] = now

            # ====================================
            # ENTRY
            # ====================================
            if not inside.get(name, False):
                inside[name] = True
                entry_time[name] = now_ts

                print(f"{name} ENTERED at {now.strftime('%H:%M:%S')}")

            # ====================================
            # EXIT
            # ====================================
            else:
                stay_total = now_ts - entry_time[name]

                if stay_total < EXIT_LOCK:
                    continue

                print(f"{name} LEFT at {now.strftime('%H:%M:%S')}")
                print("\n===== SESSION REPORT =====")

                # calculate overlap for all classes
                for i, subject in enumerate(subjects):
                    class_start = global_start + i * CLASS_DURATION
                    class_end = class_start + CLASS_DURATION

                    overlap_start = max(entry_time[name], class_start)

                    overlap_end = min(now_ts, class_end)

                    stay = max(0, overlap_end - overlap_start)

                    # add stay memory
                    prev = stay_memory[name].get(subject, 0)
                    stay_memory[name][subject] = prev + stay

                    total_subject_stay = stay_memory[name][subject]

                    # mark once
                    if total_subject_stay >= MIN_STAY and not marked[name].get(
                        subject, False
                    ):
                        cursor.execute(
                            """
                            UPDATE attendance
                            SET present_classes =
                                present_classes + 1,
                                total_classes =
                                total_classes + 1,
                                last_marked=%s
                            WHERE roll_no=%s
                            AND subject_code=%s
                        """,
                            (today, name, subject),
                        )

                        db.commit()

                        marked[name][subject] = True

                        print(
                            f"{subject} -> Total {total_subject_stay:.1f}s -> PRESENT"
                        )

                    else:
                        status = (
                            "ALREADY PRESENT"
                            if marked[name].get(subject, False)
                            else "NOT MARKED"
                        )

                        print(
                            f"{subject} -> Total {total_subject_stay:.1f}s -> {status}"
                        )

                attended = len(marked[name])

                print("==========================")
                print(f"This Session Stay: {stay_total:.1f}s")
                print(f"Overall Attendance: {attended}/4")
                print("==========================\n")

                inside[name] = False

    # ================= SCREEN =================

    cv2.putText(
        frame,
        f"Current Class: {current_subject}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
    )

    cv2.imshow("Door Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
