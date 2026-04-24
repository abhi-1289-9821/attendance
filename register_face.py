import cv2
import face_recognition
import pickle

# ================= LOAD EXISTING =================
try:
    with open("encodings.pkl", "rb") as f:
        data = pickle.load(f)
        known_encodings = data["encodings"]
        known_names = data["names"]
except:
    known_encodings = []
    known_names = []

# ================= INPUT =================
roll_no = input("Enter Roll Number: ")

# ⚠️ Prevent duplicate registration
if roll_no in known_names:
    print("⚠️ This roll number already exists!")
    exit()

cap = cv2.VideoCapture(0)
count = 0

print("📸 Press 'c' to capture (5-10 images), 'q' to quit")

# ================= CAPTURE =================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Register Face", frame)

    key = cv2.waitKey(1)

    if key == ord("c"):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)

        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(roll_no)
            count += 1
            print(f"Captured {count}")

    elif key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

# ================= SAVE =================
data = {"encodings": known_encodings, "names": known_names}

with open("encodings.pkl", "wb") as f:
    pickle.dump(data, f)

print(f"✅ {roll_no} registered with {count} samples")

# ================= VERIFY =================
print("Saved Data:", known_names)
