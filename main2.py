# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 07:55:47 2026

@author: Vikrant sinha
"""



from tkinter import *
from tkinter import messagebox, simpledialog
import os
import time
import datetime
import mysql.connector
from mysql.connector import Error
import cv2
import numpy as np
import mediapipe as mp

# =========================
# Configuration
# =========================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sanu"
}

# Change this to your project folder path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

# Global connection variable
conn = None
mycur = None


# =========================
# Helper: Convert MySQL TIME to datetime.time
# =========================
def to_time(x):
    
    if x is None:
        return None

    if isinstance(x, datetime.time):
        return x

    # MySQL sometimes returns TIME as datetime.timedelta
    if isinstance(x, datetime.timedelta):
        total_seconds = int(x.total_seconds())
        hrs = (total_seconds // 3600) % 24
        mins = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return datetime.time(hrs, mins, secs)

    # Sometimes returns string "HH:MM:SS"
    if isinstance(x, str):
        parts = x.split(":")
        return datetime.time(int(parts[0]), int(parts[1]), int(float(parts[2])))

    return None


def create_connection():
    """Create database connection with proper error handling"""
    global conn, mycur
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        mycur = conn.cursor()
        print(" Database connection established")
        return True
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to connect to database:\n{e}")
        return False


def close_connection():
    """Safely close database connection"""
    global conn, mycur
    try:
        if mycur:
            mycur.close()
        if conn and conn.is_connected():
            conn.close()
            print("Database connection closed")
    except:
        pass


def data_base():
    """Initialize database and tables"""
    try:
        mycur.execute("CREATE DATABASE IF NOT EXISTS Logi")
        mycur.execute("USE Logi")

        # User credentials table
        mycur.execute("""
        CREATE TABLE IF NOT EXISTS Logid(
            userid VARCHAR(20) PRIMARY KEY,
            password VARCHAR(20) NOT NULL,
            name VARCHAR(40) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Face registration tracking table
        mycur.execute("""
        CREATE TABLE IF NOT EXISTS face_users(
            userid VARCHAR(20) PRIMARY KEY,
            face_registered BOOLEAN DEFAULT FALSE,
            registered_at TIMESTAMP NULL,
            FOREIGN KEY (userid) REFERENCES Logid(userid) ON DELETE CASCADE
        )
        """)

        # Attendance records table
        mycur.execute("""
        CREATE TABLE IF NOT EXISTS attendance(
            id INT AUTO_INCREMENT PRIMARY KEY,
            userid VARCHAR(20),
            date DATE,
            punch_in TIME,
            punch_out TIME,
            status VARCHAR(20),
            FOREIGN KEY (userid) REFERENCES Logid(userid) ON DELETE CASCADE,
            INDEX idx_user_date (userid, date)
        )
        """)

        conn.commit()
        print("Database and tables created successfully")

    except Error as e:
        messagebox.showerror("Database Error", f"Failed to create database:\n{e}")


# =========================
# Helper Functions: Face User Registration
# =========================
def is_face_registered(userid):
    """Check if user has registered their face"""
    try:
        mycur.execute("SELECT face_registered FROM face_users WHERE userid=%s", (userid,))
        rec = mycur.fetchone()
        if rec is None:
            mycur.execute("INSERT INTO face_users(userid, face_registered) VALUES(%s,%s)", (userid, False))
            conn.commit()
            return False
        return bool(rec[0])
    except Error as e:
        messagebox.showerror("Database Error", f"Error checking face registration:\n{e}")
        return False


def set_face_registered(userid, value=True):
    """Update face registration status"""
    try:
        if value:
            mycur.execute(
                "UPDATE face_users SET face_registered=%s, registered_at=NOW() WHERE userid=%s",
                (value, userid)
            )
        else:
            mycur.execute(
                "UPDATE face_users SET face_registered=%s, registered_at=NULL WHERE userid=%s",
                (value, userid)
            )
        conn.commit()
    except Error as e:
        messagebox.showerror("Database Error", f"Error updating face registration:\n{e}")


def get_user_name(userid):
    """Get user name using userid"""
    try:
        mycur.execute("SELECT name FROM Logid WHERE userid=%s", (userid,))
        rec = mycur.fetchone()
        return rec[0] if rec else "Unknown"
    except:
        return "Unknown"


def register_face(userid, samples=25):
    """Capture face images for training"""
    os.makedirs(DATASET_DIR, exist_ok=True)
    user_folder = os.path.join(DATASET_DIR, str(userid))
    os.makedirs(user_folder, exist_ok=True)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Cannot access camera!")
        return False

    count = 0
    messagebox.showinfo("Info", "Camera will open.\nPress 'C' to capture images.\nPress 'Q' to quit.")

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        # Draw rectangles
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.putText(frame, f"User: {userid}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"Captured: {count}/{samples}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, "Press C to capture | Q to exit", (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if len(faces) > 0:
            cv2.putText(frame, "Face Detected!", (20, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "No Face Detected", (20, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Face Registration", frame)
        key = cv2.waitKey(1) & 0xFF

        if key in (ord("c"), ord("C")):
            if len(faces) > 0:
                img_path = os.path.join(user_folder, f"{count}.jpg")
                cv2.imwrite(img_path, frame)
                count += 1
                print(f"✅ Captured image {count}/{samples}")
                time.sleep(0.15)

                if count >= samples:
                    break
            else:
                print("⚠️ No face detected. Please position your face properly.")

        elif key in (ord("q"), ord("Q")):
            break

    cap.release()
    cv2.destroyAllWindows()

    if count >= samples:
        set_face_registered(userid, True)
        return True
    else:
        messagebox.showwarning("Incomplete", f"Only {count} images captured. Need {samples} for registration.")
        return False




mp_face_mesh = mp.solutions.face_mesh

def liveness_check_head_turn():
    """
    Simple anti-spoofing check using head movement.
    Randomly asks user to turn LEFT or RIGHT.
    """
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Cannot access camera!")
        return False

    challenge = np.random.choice(["LEFT", "RIGHT"])
    threshold = 0.03
    start_time = time.time()

    with mp_face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.5) as face_mesh:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = face_mesh.process(rgb)

            cv2.putText(frame, f"Liveness: Turn {challenge}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

            time_left = max(0, int(6 - (time.time() - start_time)))
            cv2.putText(frame, f"Time left: {time_left}s", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            if res.multi_face_landmarks:
                lm = res.multi_face_landmarks[0].landmark
                nose_x = lm[1].x
                left_eye_x = lm[33].x
                right_eye_x = lm[263].x
                center_x = (left_eye_x + right_eye_x) / 2
                shift = nose_x - center_x

                cv2.putText(frame, f"Shift: {shift:.3f}", (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                if challenge == "LEFT" and shift < -threshold:
                    cap.release()
                    cv2.destroyAllWindows()
                    return True

                if challenge == "RIGHT" and shift > threshold:
                    cap.release()
                    cv2.destroyAllWindows()
                    return True
            else:
                cv2.putText(frame, "No face detected!", (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if time.time() - start_time > 6:
                cap.release()
                cv2.destroyAllWindows()
                return False

            cv2.imshow("Liveness Check", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                cap.release()
                cv2.destroyAllWindows()
                return False


def train_lbph_model():
    """
    Train LBPH face recognizer using dataset images.
    Returns: (recognizer, label_map) or (None, None)
    """
    if not os.path.exists(DATASET_DIR):
        return None, None

    labels = []
    faces = []
    label_map = {}
    current_label = 0

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    for userid in os.listdir(DATASET_DIR):
        user_path = os.path.join(DATASET_DIR, userid)
        if not os.path.isdir(user_path):
            continue

        label_map[current_label] = userid
        print(f"Training for user: {userid} (label: {current_label})")

        for img_name in os.listdir(user_path):
            img_path = os.path.join(user_path, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces_rect = detector.detectMultiScale(gray, 1.2, 5)

            for (x, y, w, h) in faces_rect:
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (200, 200))
                faces.append(face_roi)
                labels.append(current_label)

        current_label += 1

    if len(faces) == 0:
        return None, None

    print(f" Training model with {len(faces)} face samples from {len(label_map)} users")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    return recognizer, label_map


def recognize_user_live(recognizer, label_map):
    """
    Live face recognition.
    Returns matched userid or None.
    """
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Cannot access camera!")
        return None

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (200, 200))

            label, confidence = recognizer.predict(face_roi)
            userid = label_map.get(label, "Unknown")

            color = (0, 255, 0) if confidence < 70 else (0, 165, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, f"ID: {userid} | Conf: {int(confidence)}",
                        (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            if confidence < 70:
                cap.release()
                cv2.destroyAllWindows()
                print(f" User recognized: {userid} (confidence: {confidence:.2f})")
                return userid

        cv2.putText(frame, "Recognizing... Press Q to exit", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        time_left = max(0, int(10 - (time.time() - start_time)))
        cv2.putText(frame, f"Time left: {time_left}s", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
            cap.release()
            cv2.destroyAllWindows()
            return None

        if time.time() - start_time > 10:
            cap.release()
            cv2.destroyAllWindows()
            return None


def mark_attendance(userid):
    """
    Mark punch-in or punch-out for the user (with fixed time handling)
    """
    try:
        today = datetime.date.today()
        now_time = datetime.datetime.now().time().replace(microsecond=0)

        mycur.execute("SELECT id, punch_in, punch_out FROM attendance WHERE userid=%s AND date=%s",
                      (userid, today))
        rec = mycur.fetchone()

        if rec is None:
            mycur.execute(
                "INSERT INTO attendance(userid, date, punch_in, punch_out, status) VALUES(%s,%s,%s,%s,%s)",
                (userid, today, now_time, None, "PRESENT")
            )
            conn.commit()
            return f" Punch-IN marked at {now_time}"

        att_id, punch_in, punch_out = rec

        punch_in = to_time(punch_in)
        punch_out = to_time(punch_out)

        if punch_out is None:
            mycur.execute("UPDATE attendance SET punch_out=%s WHERE id=%s",
                          (now_time, att_id))
            conn.commit()

            if punch_in is not None:
                duration = datetime.datetime.combine(today, now_time) - datetime.datetime.combine(today, punch_in)
                hours = duration.total_seconds() / 3600
                return f" Punch-OUT marked at {now_time}\nWork duration: {hours:.2f} hours"
            else:
                return f" Punch-OUT marked at {now_time}"

        return " Attendance already completed for today"

    except Error as e:
        messagebox.showerror("Database Error", f"Error marking attendance:\n{e}")
        return " Failed to mark attendance"


def view_attendance(userid):
    """Display user's attendance history (FIXED time handling)"""
    try:
        root_view = Tk()
        root_view.title("Attendance Records")
        root_view.geometry("850x520+300+100")
        root_view.configure(bg="white")

        Label(root_view, text="Your Attendance Records", bg="white", fg="teal",
              font="arial 16 bold").pack(pady=20)

        frame = Frame(root_view, bg="white")
        frame.pack(pady=10, padx=20, fill=BOTH, expand=True)

        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        text_box = Text(frame, yscrollcommand=scrollbar.set, font="courier 10",
                        height=20, width=95, bg="lightyellow")
        text_box.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=text_box.yview)

        mycur.execute("""
            SELECT date, punch_in, punch_out, status
            FROM attendance
            WHERE userid=%s
            ORDER BY date DESC
            LIMIT 30
        """, (userid,))
        records = mycur.fetchall()

        if records:
            text_box.insert(END, f"{'Date':<15} {'Punch-IN':<12} {'Punch-OUT':<12} {'Status':<10} {'Duration':<10}\n")
            text_box.insert(END, "=" * 85 + "\n")

            for date, punch_in, punch_out, status in records:
                punch_in_t = to_time(punch_in)
                punch_out_t = to_time(punch_out)

                duration = "N/A"
                if punch_in_t and punch_out_t:
                    delta = datetime.datetime.combine(date, punch_out_t) - datetime.datetime.combine(date, punch_in_t)
                    hours = delta.total_seconds() / 3600
                    duration = f"{hours:.2f}h"

                punch_in_str = str(punch_in_t) if punch_in_t else "N/A"
                punch_out_str = str(punch_out_t) if punch_out_t else "N/A"

                text_box.insert(END, f"{str(date):<15} {punch_in_str:<12} {punch_out_str:<12} {status:<10} {duration:<10}\n")
        else:
            text_box.insert(END, "\nNo attendance records found.")

        text_box.config(state=DISABLED)

        Button(root_view, text="Close", command=root_view.destroy,
               width=15, bg="red", fg="white", font="arial 12 bold").pack(pady=10)

        root_view.mainloop()

    except Error as e:
        messagebox.showerror("Database Error", f"Error fetching attendance:\n{e}")


def view_all_attendance():
    """Admin: View attendance records for all users"""
    try:
        # Optional admin password
        pwd = simpledialog.askstring("Admin Access", "Enter Admin Password:", show="*")
        if pwd != "admin123":
            messagebox.showerror("Denied", " Wrong admin password!")
            return

        root_view = Tk()
        root_view.title("All Attendance Records")
        root_view.geometry("1050x560+250+80")
        root_view.configure(bg="white")

        Label(root_view, text="All Attendance Records (Admin)", bg="white", fg="teal",
              font="arial 16 bold").pack(pady=20)

        frame = Frame(root_view, bg="white")
        frame.pack(pady=10, padx=20, fill=BOTH, expand=True)

        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        text_box = Text(frame, yscrollcommand=scrollbar.set, font="courier 10",
                        height=22, width=130, bg="lightyellow")
        text_box.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=text_box.yview)

        mycur.execute("""
            SELECT a.date, a.userid, l.name, a.punch_in, a.punch_out, a.status
            FROM attendance a
            JOIN Logid l ON a.userid = l.userid
            ORDER BY a.date DESC, a.userid ASC
            LIMIT 250
        """)
        records = mycur.fetchall()

        if records:
            text_box.insert(END, f"{'Date':<12} {'UserID':<12} {'Name':<20} {'IN':<10} {'OUT':<10} {'Duration':<10} {'Status':<10}\n")
            text_box.insert(END, "=" * 100 + "\n")

            for date, userid, name, punch_in, punch_out, status in records:
                pin = to_time(punch_in)
                pout = to_time(punch_out)

                duration = "N/A"
                if pin and pout:
                    delta = datetime.datetime.combine(date, pout) - datetime.datetime.combine(date, pin)
                    duration = f"{delta.total_seconds()/3600:.2f}h"

                pin_str = str(pin) if pin else "N/A"
                pout_str = str(pout) if pout else "N/A"

                text_box.insert(
                    END,
                    f"{str(date):<12} {userid:<12} {name[:18]:<20} {pin_str:<10} {pout_str:<10} {duration:<10} {status:<10}\n"
                )
        else:
            text_box.insert(END, "\nNo attendance records found.")

        text_box.config(state=DISABLED)

        Button(root_view, text="Close", command=root_view.destroy,
               width=15, bg="red", fg="white", font="arial 12 bold").pack(pady=10)

        root_view.mainloop()

    except Error as e:
        messagebox.showerror("Database Error", f"Error fetching all attendance:\n{e}")


def start_attendance_workflow():
    """Workflow: Liveness -> Recognition -> Attendance"""
    print("Starting liveness check...")
    ok = liveness_check_head_turn()
    if not ok:
        messagebox.showerror("Failed", " Liveness check failed!\nPlease try again.")
        return

    print("Training recognition model...")
    recognizer, label_map = train_lbph_model()
    if recognizer is None:
        messagebox.showerror("Error", "No registered faces found.\nPlease register face first.")
        return

    print("Starting face recognition...")
    userid = recognize_user_live(recognizer, label_map)
    if userid is None:
        messagebox.showerror("Failed", " Face not recognized!\nPlease try again.")
        return

    msg = mark_attendance(userid)
    uname = get_user_name(userid)
    messagebox.showinfo("Attendance", f"{msg}\n\nUser: {uname} ({userid})")


def quick_punch_mode():
    """No login required: Liveness -> Recognition -> Punch"""
    if not os.path.exists(DATASET_DIR):
        messagebox.showerror("Error", "No face dataset found.\nRegister users first via Login.")
        return
    start_attendance_workflow()


def attendance_dashboard(userid, username):
    """Dashboard after successful login"""
    root_dash = Tk()
    root_dash.title("Face Attendance Dashboard")
    root_dash.geometry("650x570+350+90")
    root_dash.configure(bg="teal")

    Label(root_dash, text="Face Attendance System", bg="teal", fg="yellow",
          font="arial 20 bold italic").pack(pady=20)

    Label(root_dash, text=f"Welcome, {username}!", bg="teal", fg="white",
          font="arial 14 bold").pack(pady=5)

    Label(root_dash, text=f"User ID: {userid}", bg="teal", fg="lightgray",
          font="arial 11").pack(pady=5)

    is_registered = is_face_registered(userid)
    status_text = " Face Registered" if is_registered else "⚠️ Face Not Registered"
    status_color = "lightgreen" if is_registered else "orange"

    Label(root_dash, text=status_text, bg="teal", fg=status_color,
          font="arial 12 bold").pack(pady=10)

    def do_register_face():
        done = register_face(userid, samples=25)
        if done:
            messagebox.showinfo("Success", " Face registered successfully!\nNow use Punch IN/OUT.")
            root_dash.destroy()
            attendance_dashboard(userid, username)
        else:
            messagebox.showwarning("Incomplete", "⚠️ Face registration incomplete!\nPlease try again.")

    def do_mark_attendance():
        if not is_face_registered(userid):
            messagebox.showwarning("Not Registered", "⚠️ Please register your face first!")
            return
        start_attendance_workflow()

    def do_view_attendance():
        view_attendance(userid)

    Button(root_dash, text="Register/Update Face", command=do_register_face,
           width=30, bg="yellow", font="arial 12 bold", cursor="hand2").pack(pady=10)

    Button(root_dash, text="Punch IN / OUT", command=do_mark_attendance,
           width=30, bg="lightgreen", font="arial 12 bold", cursor="hand2").pack(pady=10)

    Button(root_dash, text="View Attendance History", command=do_view_attendance,
           width=30, bg="lightblue", font="arial 12 bold", cursor="hand2").pack(pady=10)

    Button(root_dash, text="Logout", command=root_dash.destroy,
           width=30, bg="red", fg="white", font="arial 12 bold", cursor="hand2").pack(pady=10)

    info_text = """
Instructions:
1. Register your face (one-time setup)
2. Use Punch IN/OUT for daily attendance
3. Liveness check blocks phone/printed photo spoofing
"""
    Label(root_dash, text=info_text, bg="teal", fg="white",
          font="arial 9", justify=LEFT).pack(pady=12)

    root_dash.mainloop()


def register():
    """User registration window"""
    root4 = Tk()
    root4.title("Face Attendance System - Signup")
    root4.geometry("600x550+400+100")
    root4.configure(bg="teal")

    Label(root4, text="User Registration", bg="teal", fg="yellow",
          font="arial 20 bold italic").place(x=160, y=20)

    Label(root4, text="User ID:", bg="teal", fg="white", font="arial 14 bold").place(x=80, y=120)
    Label(root4, text="Password:", bg="teal", fg="white", font="arial 14 bold").place(x=80, y=180)
    Label(root4, text="Full Name:", bg="teal", fg="white", font="arial 14 bold").place(x=80, y=240)

    a1 = StringVar()
    a2 = StringVar()
    a3 = StringVar()

    Entry(root4, textvariable=a1, width=25, font="arial 12").place(x=250, y=120)
    Entry(root4, textvariable=a2, width=25, font="arial 12", show="*").place(x=250, y=180)
    Entry(root4, textvariable=a3, width=25, font="arial 12").place(x=250, y=240)

    def signup():
        uid = a1.get().strip()
        pw = a2.get().strip()
        name = a3.get().strip()

        if uid == "" or pw == "" or name == "":
            messagebox.showerror("Error", "All fields are required!")
            return

        if len(uid) < 3 or len(uid) > 20:
            messagebox.showerror("Error", "User ID must be 3-20 characters!")
            return

        if len(pw) < 6 or len(pw) > 20:
            messagebox.showerror("Error", "Password must be 6-20 characters!")
            return

        if not uid.isalnum():
            messagebox.showerror("Error", "User ID must be alphanumeric!")
            return

        try:
            mycur.execute("INSERT INTO Logid(userid, password, name) VALUES(%s,%s,%s)", (uid, pw, name))
            conn.commit()

            mycur.execute("INSERT INTO face_users(userid, face_registered) VALUES(%s,%s)", (uid, False))
            conn.commit()

            messagebox.showinfo("Success", " Registration successful!\nPlease login to continue.")
            root4.destroy()
            main()

        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "User ID already exists!")
        except Error as e:
            messagebox.showerror("Database Error", f"Registration failed:\n{e}")

    def clear():
        a1.set("")
        a2.set("")
        a3.set("")

    def back_to_login():
        root4.destroy()
        main()

    Button(root4, text="Register", command=signup, width=10,
           bg="lightgreen", font="arial 12 bold", cursor="hand2").place(x=150, y=350)

    Button(root4, text="Clear", command=clear, width=10,
           bg="orange", font="arial 12 bold", cursor="hand2").place(x=280, y=350)

    Button(root4, text="Back to Login", command=back_to_login, width=12,
           bg="lightblue", font="arial 12 bold", cursor="hand2").place(x=400, y=350)

    root4.mainloop()


# =======================
def main():
    """Main login window"""
    root = Tk()
    root.title("Face Attendance System - Login")
    root.geometry("650x600+350+80")
    root.configure(bg="teal")

    Label(root, text="FACE ATTENDANCE SYSTEM", bg="teal", fg="yellow",
          font="arial 22 bold italic").place(x=80, y=25)

    Label(root, text="Login to Your Account", bg="teal", fg="white",
          font="arial 14 italic").place(x=220, y=95)

    Label(root, text="User ID:", bg="teal", fg="white", font="arial 14 bold").place(x=100, y=170)
    Label(root, text="Password:", bg="teal", fg="white", font="arial 14 bold").place(x=100, y=230)

    v1 = StringVar()
    v2 = StringVar()

    Entry(root, textvariable=v1, width=25, font="arial 12").place(x=250, y=170)
    Entry(root, textvariable=v2, show="●", width=25, font="arial 12").place(x=250, y=230)

    def close():
        if messagebox.askokcancel("Quit", "Do you want to exit?"):
            root.destroy()
            close_connection()

    def clear():
        v1.set("")
        v2.set("")

    def login():
        uid = v1.get().strip()
        pw = v2.get().strip()

        if uid == "" or pw == "":
            messagebox.showerror("Error", "Please enter both User ID and Password!")
            return

        try:
            mycur.execute("SELECT userid, password, name FROM Logid WHERE userid=%s", (uid,))
            rec = mycur.fetchone()

            if rec is None:
                messagebox.showerror("Error", "User not found!\nPlease register first.")
                return

            db_uid, db_pw, db_name = rec
            if pw == db_pw:
                messagebox.showinfo("Success", f" Welcome, {db_name}!")
                root.destroy()
                attendance_dashboard(uid, db_name)
            else:
                messagebox.showerror("Error", "Incorrect password!")
                clear()

        except Error as e:
            messagebox.showerror("Database Error", f"Login failed:\n{e}")

    def open_register():
        root.destroy()
        register()

    # ===== Buttons =====
    Button(root, text="Login", command=login, width=12,
           bg="lightgreen", fg="black", font="arial 13 bold", cursor="hand2").place(x=200, y=310)

    Button(root, text="Clear", command=clear, width=12,
           bg="orange", fg="black", font="arial 13 bold", cursor="hand2").place(x=350, y=310)

    Button(root, text="New User? Sign Up", command=open_register,
           bg="lightblue", fg="black", font="arial 11 bold", cursor="hand2").place(x=220, y=370)

    Button(root, text="Quick Punch IN/OUT (No Login)", command=quick_punch_mode,
           bg="yellow", fg="black", font="arial 12 bold", cursor="hand2").place(x=175, y=430)

    Button(root, text="View Full Attendance (Admin)", command=view_all_attendance,
           bg="lightgray", fg="black", font="arial 12 bold", cursor="hand2").place(x=195, y=485)

    Button(root, text="Exit", command=close, width=12,
           bg="red", fg="white", font="arial 13 bold", cursor="hand2").place(x=270, y=540)

    info_text = "Secure Face Recognition Attendance System"
    Label(root, text=info_text, bg="teal", fg="lightgray",
          font="arial 9 italic").place(x=200, y=575)

    root.protocol("WM_DELETE_WINDOW", close)
    root.mainloop()


# =========================
# Main Entry Point
# =========================
if __name__ == "__main__":
    os.makedirs(DATASET_DIR, exist_ok=True)

    if create_connection():
        data_base()
        main()
    else:
        print(" Failed to start application due to database connection error")
