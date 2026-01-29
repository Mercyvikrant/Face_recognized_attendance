# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 07:30:09 2026

@author: Vikrant sinha
"""

# -*- coding: utf-8 -*-
"""
Face Recognition Attendance System (Debugged & Improved)
Author: Vikrant sinha (Improved by Claude)
Features:
- User registration and login
- Face registration with live capture
- Anti-spoofing liveness detection
- Face recognition for punch in/out
- MySQL database for user and attendance management
"""

from tkinter import *
from tkinter import messagebox
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
    'host': 'localhost',
    'user': 'root',
    'password': 'sanu'  # Change this to your MySQL password
}

# Global connection variable
conn = None
mycur = None


# =========================
# MySQL Connection with Error Handling
# =========================
def create_connection():
    """Create database connection with proper error handling"""
    global conn, mycur
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        mycur = conn.cursor()
        print("✅ Database connection established")
        return True
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to connect to database:\n{e}")
        return False


def close_connection():
    """Safely close database connection"""
    global conn, mycur
    if mycur:
        mycur.close()
    if conn and conn.is_connected():
        conn.close()
        print("✅ Database connection closed")


# =========================
# Database Setup
# =========================
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
        print("✅ Database and tables created successfully")

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
            # Create row if missing
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
            mycur.execute("UPDATE face_users SET face_registered=%s, registered_at=NOW() WHERE userid=%s", 
                         (value, userid))
        else:
            mycur.execute("UPDATE face_users SET face_registered=%s, registered_at=NULL WHERE userid=%s", 
                         (value, userid))
        conn.commit()
    except Error as e:
        messagebox.showerror("Database Error", f"Error updating face registration:\n{e}")


# =========================
# Face Registration
# =========================
def register_face(userid, samples=25):
    """Capture face images for training"""
    os.makedirs("D:\\Face_recognized_attendance\\dataset", exist_ok=True)
    user_folder = os.path.join("D:\\Face_recognized_attendance\\dataset", str(userid))
    os.makedirs(user_folder, exist_ok=True)

    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Cannot access camera!")
        return False
    
    count = 0
    messagebox.showinfo("Info", "Camera will open.\nPress 'C' to capture images.\nPress 'Q' to quit.")

    # Initialize face detector for better quality check
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        # Draw rectangle around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Display information
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

        if key == ord("c") or key == ord("C"):
            if len(faces) > 0:  # Only capture if face is detected
                img_path = os.path.join(user_folder, f"{count}.jpg")
                cv2.imwrite(img_path, frame)
                count += 1
                print(f"✅ Captured image {count}/{samples}")
                time.sleep(0.15)

                if count >= samples:
                    break
            else:
                print("⚠️ No face detected. Please position your face properly.")

        elif key == ord("q") or key == ord("Q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    if count >= samples:
        set_face_registered(userid, True)
        return True
    else:
        messagebox.showwarning("Incomplete", f"Only {count} images captured. Need {samples} for registration.")
        return False


# =========================
# Liveness Check (Anti-Spoof)
# =========================
mp_face_mesh = mp.solutions.face_mesh

def liveness_check_head_turn():
    """
    Simple anti-spoofing check using head movement
    Randomly asks user to turn LEFT or RIGHT
    """
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Cannot access camera!")
        return False
    
    challenge = np.random.choice(["LEFT", "RIGHT"])
    threshold = 0.03  # Adjust sensitivity (0.02 to 0.05)
    start_time = time.time()

    with mp_face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.5) as face_mesh:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = face_mesh.process(rgb)

            cv2.putText(frame, f"Liveness Check: Turn {challenge}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            
            time_left = int(6 - (time.time() - start_time))
            cv2.putText(frame, f"Time left: {time_left}s", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            if res.multi_face_landmarks:
                lm = res.multi_face_landmarks[0].landmark

                # Landmarks: nose tip(1), left eye outer(33), right eye outer(263)
                nose_x = lm[1].x
                left_eye_x = lm[33].x
                right_eye_x = lm[263].x
                center_x = (left_eye_x + right_eye_x) / 2

                shift = nose_x - center_x

                # Display current shift for debugging
                cv2.putText(frame, f"Shift: {shift:.3f}", (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                # LEFT means nose shifts negative, RIGHT means positive
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

            # Timeout after 6 seconds
            if time.time() - start_time > 6:
                cap.release()
                cv2.destroyAllWindows()
                return False

            cv2.imshow("Liveness Check", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                cap.release()
                cv2.destroyAllWindows()
                return False


# =========================
# Face Recognition (LBPH)
# =========================
def train_lbph_model():
    """
    Train LBPH face recognizer using dataset images
    Returns: (recognizer, label_map) or (None, None) if no data
    """
    dataset_dir = "D:\\Face_recognized_attendance\\dataset"
    if not os.path.exists(dataset_dir):
        return None, None

    labels = []
    faces = []
    label_map = {}  # maps numeric label -> userid
    current_label = 0

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    for userid in os.listdir(dataset_dir):
        user_path = os.path.join(dataset_dir, userid)
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

    print(f"✅ Training model with {len(faces)} face samples from {len(label_map)} users")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    return recognizer, label_map


def recognize_user_live(recognizer, label_map):
    """
    Perform live face recognition
    Returns: matched userid or None
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

            # Lower confidence = better match in LBPH (0 = perfect match)
            color = (0, 255, 0) if confidence < 70 else (0, 165, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, f"ID: {userid} | Conf: {int(confidence)}",
                        (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Confidence threshold (lower is better, typically 0-100)
            if confidence < 70:
                cap.release()
                cv2.destroyAllWindows()
                print(f"✅ User recognized: {userid} (confidence: {confidence:.2f})")
                return userid

        # Display instructions
        cv2.putText(frame, "Recognizing... Press Q to exit", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        time_left = int(10 - (time.time() - start_time))
        cv2.putText(frame, f"Time left: {time_left}s", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            return None

        # Timeout after 10 seconds
        if time.time() - start_time > 10:
            cap.release()
            cv2.destroyAllWindows()
            return None


# =========================
# Attendance Logic
# =========================
def mark_attendance(userid):
    """
    Mark punch-in or punch-out for the user
    """
    try:
        today = datetime.date.today()
        now_time = datetime.datetime.now().time().replace(microsecond=0)

        mycur.execute("SELECT id, punch_in, punch_out FROM attendance WHERE userid=%s AND date=%s",
                      (userid, today))
        rec = mycur.fetchone()

        if rec is None:
            # First punch of the day - mark punch-in
            mycur.execute(
                "INSERT INTO attendance(userid, date, punch_in, punch_out, status) VALUES(%s,%s,%s,%s,%s)",
                (userid, today, now_time, None, "PRESENT")
            )
            conn.commit()
            return f"✅ Punch-IN marked at {now_time}"

        att_id, punch_in, punch_out = rec
        if punch_out is None:
            # Already punched in, now mark punch-out
            mycur.execute("UPDATE attendance SET punch_out=%s WHERE id=%s",
                          (now_time, att_id))
            conn.commit()
            duration = datetime.datetime.combine(today, now_time) - datetime.datetime.combine(today, punch_in)
            hours = duration.total_seconds() / 3600
            return f"✅ Punch-OUT marked at {now_time}\nWork duration: {hours:.2f} hours"

        return "⚠️ Attendance already completed for today"

    except Error as e:
        messagebox.showerror("Database Error", f"Error marking attendance:\n{e}")
        return "❌ Failed to mark attendance"


# =========================
# View Attendance Records
# =========================
def view_attendance(userid):
    """Display user's attendance history"""
    try:
        root_view = Tk()
        root_view.title("Attendance Records")
        root_view.geometry("800x500+300+100")
        root_view.configure(bg="white")

        Label(root_view, text="Your Attendance Records", bg="white", fg="teal",
              font="arial 16 bold").pack(pady=20)

        # Create frame for scrollable text
        frame = Frame(root_view, bg="white")
        frame.pack(pady=10, padx=20, fill=BOTH, expand=True)

        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        text_box = Text(frame, yscrollcommand=scrollbar.set, font="courier 10",
                        height=20, width=90, bg="lightyellow")
        text_box.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=text_box.yview)

        # Fetch attendance records
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
            text_box.insert(END, "="*80 + "\n")

            for date, punch_in, punch_out, status in records:
                duration = "N/A"
                if punch_in and punch_out:
                    delta = datetime.datetime.combine(date, punch_out) - datetime.datetime.combine(date, punch_in)
                    hours = delta.total_seconds() / 3600
                    duration = f"{hours:.2f}h"

                punch_in_str = str(punch_in) if punch_in else "N/A"
                punch_out_str = str(punch_out) if punch_out else "N/A"

                text_box.insert(END, f"{date!s:<15} {punch_in_str:<12} {punch_out_str:<12} {status:<10} {duration:<10}\n")
        else:
            text_box.insert(END, "\nNo attendance records found.")

        text_box.config(state=DISABLED)

        Button(root_view, text="Close", command=root_view.destroy,
               width=15, bg="red", fg="white", font="arial 12 bold").pack(pady=10)

        root_view.mainloop()

    except Error as e:
        messagebox.showerror("Database Error", f"Error fetching attendance:\n{e}")


# =========================
# Attendance Workflow
# =========================
def start_attendance_workflow():
    """Main workflow: Liveness -> Recognition -> Attendance"""
    # Step 1: Liveness check
    print("Starting liveness check...")
    ok = liveness_check_head_turn()
    if not ok:
        messagebox.showerror("Failed", "❌ Liveness check failed!\nPlease try again.")
        return

    # Step 2: Train model
    print("Training recognition model...")
    recognizer, label_map = train_lbph_model()
    if recognizer is None:
        messagebox.showerror("Error", "No registered faces found.\nPlease register your face first.")
        return

    # Step 3: Recognize user
    print("Starting face recognition...")
    userid = recognize_user_live(recognizer, label_map)
    if userid is None:
        messagebox.showerror("Failed", "❌ Face not recognized!\nPlease try again.")
        return

    # Step 4: Mark attendance
    msg = mark_attendance(userid)
    messagebox.showinfo("Attendance", f"{msg}\n\nUser: {userid}")


# =========================
# Attendance Dashboard
# =========================
def attendance_dashboard(userid, username):
    """Dashboard after successful login"""
    root_dash = Tk()
    root_dash.title("Face Attendance Dashboard")
    root_dash.geometry("650x550+350+100")
    root_dash.configure(bg="teal")

    Label(root_dash, text="Face Attendance System", bg="teal", fg="yellow",
          font="arial 20 bold italic").pack(pady=20)

    Label(root_dash, text=f"Welcome, {username}!", bg="teal", fg="white",
          font="arial 14 bold").pack(pady=5)
    
    Label(root_dash, text=f"User ID: {userid}", bg="teal", fg="lightgray",
          font="arial 11").pack(pady=5)

    # Check face registration status
    is_registered = is_face_registered(userid)
    status_text = "✅ Face Registered" if is_registered else "⚠️ Face Not Registered"
    status_color = "lightgreen" if is_registered else "orange"
    
    Label(root_dash, text=status_text, bg="teal", fg=status_color,
          font="arial 12 bold").pack(pady=10)

    # Buttons frame
    button_frame = Frame(root_dash, bg="teal")
    button_frame.pack(pady=20)

    def do_register_face():
        done = register_face(userid, samples=25)
        if done:
            messagebox.showinfo("Success", "✅ Face registered successfully!\nYou can now use Punch IN/OUT.")
            root_dash.destroy()
            attendance_dashboard(userid, username)  # Refresh dashboard
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

    # Instructions
    info_text = """
    Instructions:
    1. Register your face (one-time setup)
    2. Use Punch IN/OUT for daily attendance
    3. Liveness check will verify you're not using a photo
    4. View your attendance history anytime
    """
    Label(root_dash, text=info_text, bg="teal", fg="white",
          font="arial 9", justify=LEFT).pack(pady=10)

    root_dash.mainloop()


# =========================
# Registration Window
# =========================
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

    # Info labels
    Label(root4, text="(alphanumeric, 3-20 chars)", bg="teal", fg="lightgray",
          font="arial 9 italic").place(x=250, y=145)
    Label(root4, text="(6-20 chars)", bg="teal", fg="lightgray",
          font="arial 9 italic").place(x=250, y=205)

    def signup():
        uid = a1.get().strip()
        pw = a2.get().strip()
        name = a3.get().strip()

        # Validation
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
            # Insert user
            query = "INSERT INTO Logid(userid, password, name) VALUES(%s,%s,%s)"
            mycur.execute(query, (uid, pw, name))
            conn.commit()

            # Create face_users record
            mycur.execute("INSERT INTO face_users(userid, face_registered) VALUES(%s,%s)", (uid, False))
            conn.commit()

            messagebox.showinfo("Success", "✅ Registration successful!\nPlease login to continue.")
            root4.destroy()
            main()

        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "User ID already exists!\nPlease choose a different ID.")
        except Error as e:
            messagebox.showerror("Database Error", f"Registration failed:\n{e}")

    def clear():
        a1.set("")
        a2.set("")
        a3.set("")

    def close():
        root4.destroy()
        main()

    # Buttons
    Button(root4, text="Register", command=signup, width=10,
           bg="lightgreen", fg="black", font="arial 12 bold", cursor="hand2").place(x=150, y=350)
    Button(root4, text="Clear", command=clear, width=10,
           bg="orange", fg="black", font="arial 12 bold", cursor="hand2").place(x=280, y=350)
    Button(root4, text="Back to Login", command=close, width=12,
           bg="lightblue", fg="black", font="arial 12 bold", cursor="hand2").place(x=400, y=350)

    root4.mainloop()


# =========================
# Main Login Window
# =========================
def main():
    """Main login window"""
    root = Tk()
    root.title("Face Attendance System - Login")
    root.geometry("650x550+350+100")
    root.configure(bg="teal")

    Label(root, text="FACE ATTENDANCE SYSTEM", bg="teal", fg="yellow",
          font="arial 22 bold italic").place(x=80, y=30)

    Label(root, text="Login to Your Account", bg="teal", fg="white",
          font="arial 14 italic").place(x=220, y=100)

    Label(root, text="User ID:", bg="teal", fg="white", font="arial 14 bold").place(x=100, y=180)
    Label(root, text="Password:", bg="teal", fg="white", font="arial 14 bold").place(x=100, y=240)

    v1 = StringVar()
    v2 = StringVar()

    Entry(root, textvariable=v1, width=25, font="arial 12").place(x=250, y=180)
    Entry(root, textvariable=v2, show="●", width=25, font="arial 12").place(x=250, y=240)

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
                messagebox.showinfo("Success", f"✅ Welcome, {db_name}!")
                root.destroy()
                attendance_dashboard(uid, db_name)
            else:
                messagebox.showerror("Error", "Incorrect password!")
                clear()

        except Error as e:
            messagebox.showerror("Database Error", f"Login failed:\n{e}")

    def register_close():
        root.destroy()
        register()

    # Buttons
    Button(root, text="Login", command=login, width=12,
           bg="lightgreen", fg="black", font="arial 13 bold", cursor="hand2").place(x=200, y=320)

    Button(root, text="Clear", command=clear, width=12,
           bg="orange", fg="black", font="arial 13 bold", cursor="hand2").place(x=350, y=320)

    Button(root, text="New User? Sign Up", command=register_close,
           bg="lightblue", fg="black", font="arial 11 bold", cursor="hand2").place(x=220, y=380)

    Button(root, text="Exit", command=close, width=12,
           bg="red", fg="white", font="arial 13 bold", cursor="hand2").place(x=270, y=440)

    # Info
    info_text = "Secure Face Recognition Attendance System"
    Label(root, text=info_text, bg="teal", fg="lightgray",
          font="arial 9 italic").place(x=180, y=500)

    root.protocol("WM_DELETE_WINDOW", close)
    root.mainloop()


# =========================
# Main Entry Point
# =========================
if __name__ == "__main__":
    if create_connection():
        data_base()
        main()
    else:
        print("❌ Failed to start application due to database connection error")