# app.py

from flask import Flask, render_template, request, redirect, session
import mysql.connector
import cv2
import face_recognition
import pickle
import os
import base64
import numpy as np

app = Flask(__name__)
app.secret_key = ".env"

# ================= MYSQL =================

db = mysql.connector.connect(
    host="localhost",
    user="attendance_user",
    password=".env",
    database="face_attendance",
    auth_plugin=".env",
)

cursor = db.cursor()

# ================= FACE FOLDER =================

if not os.path.exists("static/faces"):
    os.makedirs("static/faces")

# ================= LOGIN =================


@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        cursor.execute(
            "SELECT roll_no FROM users WHERE email=%s AND password=%s",
            (email, password),
        )

        user = cursor.fetchone()

        if user:
            session["roll_no"] = user[0]
            return redirect("/dashboard")

        return "Invalid Email or Password"

    return render_template("login.html")


# ================= REGISTER =================


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form["name"].strip().upper()
        roll_no = request.form["roll_no"].strip().upper()
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        image_data = request.form["image"]

        # basic validation
        if len(roll_no) < 5:
            return "Invalid Roll Number"

        # duplicate roll check
        cursor.execute("SELECT roll_no FROM students WHERE roll_no=%s", (roll_no,))

        if cursor.fetchone():
            return "Roll Number Already Registered"

        # duplicate email check
        cursor.execute("SELECT email FROM users WHERE email=%s", (email,))

        if cursor.fetchone():
            return "Email Already Registered"

        # ================= IMAGE =================

        if "," not in image_data:
            return "Capture Face First"

        image_data = image_data.split(",")[1]

        img_bytes = base64.b64decode(image_data)

        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        file_path = f"static/faces/{roll_no}.jpg"
        cv2.imwrite(file_path, img)

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        encodings = face_recognition.face_encodings(rgb)

        if len(encodings) == 0:
            return "No Face Detected"

        face_encoding = encodings[0]

        # ================= PKL UPDATE =================

        if os.path.exists("encodings.pkl"):
            with open("encodings.pkl", "rb") as f:
                data = pickle.load(f)

            known_encodings = data["encodings"]
            known_names = data["names"]

        else:
            known_encodings = []
            known_names = []

        known_encodings.append(face_encoding)
        known_names.append(roll_no.lower())

        with open("encodings.pkl", "wb") as f:
            pickle.dump({"encodings": known_encodings, "names": known_names}, f)

        # ================= DB INSERT =================

        cursor.execute(
            "INSERT INTO students (roll_no,name) VALUES (%s,%s)", (roll_no, name)
        )

        cursor.execute(
            "INSERT INTO users (email,password,roll_no) VALUES (%s,%s,%s)",
            (email, password, roll_no),
        )

        cursor.execute("SELECT subject_code FROM subjects")
        subjects = cursor.fetchall()

        for sub in subjects:
            cursor.execute(
                """
                INSERT INTO attendance
                (roll_no,subject_code,present_classes,total_classes)
                VALUES (%s,%s,0,0)
            """,
                (roll_no, sub[0]),
            )

        db.commit()

        return redirect("/")

    return render_template("register.html")


# ================= DASHBOARD =================


@app.route("/dashboard")
def dashboard():

    if "roll_no" not in session:
        return redirect("/")

    roll_no = session["roll_no"]

    cursor.execute(
        """
        SELECT
            s.subject_code,
            s.subject_name,
            s.faculty_name,
            a.present_classes,
            a.total_classes
        FROM attendance a
        JOIN subjects s
        ON a.subject_code=s.subject_code
        WHERE a.roll_no=%s
    """,
        (roll_no,),
    )

    rows = cursor.fetchall()

    data = []
    tp = 0
    tc = 0

    for row in rows:
        present = row[3]
        total = row[4]

        percent = 0 if total == 0 else round((present / total) * 100, 2)

        data.append((row[0], row[1], row[2], present, total, percent))

        tp += present
        tc += total

    overall = None if tc == 0 else round((tp / tc) * 100, 2)

    return render_template("dashboard.html", data=data, overall=overall)


# ================= LOGOUT =================


@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
