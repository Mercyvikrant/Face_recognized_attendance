# Face_recognized_attendance
Help in attendance as in punch in and out systems and have regular databse  using which one can take care of daily activity of office workers

#First Page
<img width="813" height="788" alt="image" src="https://github.com/user-attachments/assets/5b7555e7-153a-4457-98fe-550213eb9bd6" />

# after login page
<img width="808" height="718" alt="image" src="https://github.com/user-attachments/assets/d14022f9-b478-494a-a510-d71e453b79c3" />

# now attendance view page
<img width="1057" height="670" alt="image" src="https://github.com/user-attachments/assets/0a17bdad-d98b-4225-b71d-2fe4babe18c0"/>



# SEE VIDEO FOR DEMONSTRATION
https://drive.google.com/file/d/1zcNZDTKZqzzoUo1c7YqOnVBU5YuR8OJI/view?usp=sharing



# Face Authentication Attendance System (Tkinter + OpenCV + MySQL)

A desktop-based **Face Authentication Attendance System** built using **Python**, **Tkinter**, **OpenCV**, **MySQL**, and **MediaPipe**.  
The system allows users to register their face once and then mark daily attendance using **Punch-In** and **Punch-Out** with real-time camera input.

This project also includes a **basic spoof prevention mechanism** to reduce false attendance using photos from mobile screens or printed images.

---

## ✅ Features

### ✅ User Management
- Register new users (UserID + Password + Name)
- Login using MySQL stored credentials

### ✅ Face Registration
- Register a user’s face (one-time setup)
- Captures **multiple face samples** from a live webcam
- Stores face samples locally in a dataset directory:


### ✅ Face Recognition Attendance
- Works with **real-time camera input**
- Recognizes registered faces and automatically updates attendance:
- ✅ Punch-In
- ✅ Punch-Out

### ✅ Attendance Record Management
- Stores attendance records in MySQL
- View attendance history for a user
- View full attendance records (admin view)

### ✅ Spoof Prevention (Photo Attack Fix)
To reduce spoofing attempts (example: showing a photo from a phone screen),
this project implements a **basic liveness detection technique** using head movement:
- User is asked to turn their head **LEFT** or **RIGHT**
- The system checks nose position movement using **MediaPipe FaceMesh landmarks**
- Prevents simple spoofing using static images (mobile photo / hardcopy)

---

## 🛠 Tech Stack / Libraries Used

| Component | Technology |
|----------|------------|
| Language | Python |
| GUI | Tkinter |
| Camera + Vision | OpenCV |
| Face Recognition | LBPH (OpenCV) |
| Spoof Detection | MediaPipe FaceMesh |
| Database | MySQL |
| DB Connector | mysql-connector-python |

---

## ✅ Project Workflow

### 1️⃣ Signup
- User creates an account using Tkinter UI
- Data is stored in MySQL (`Logid` table)

### 2️⃣ Login
- User logs in using registered credentials

### 3️⃣ Face Registration (One-Time Only)
- Webcam opens and captures face images
- Saved under:


### 4️⃣ Attendance Marking (Daily)
- Webcam opens
- Liveness check runs (head turn)
- Face is recognized using LBPH model
- Attendance updated:
- If no record exists today → ✅ Punch-In
- If Punch-In exists but Punch-Out missing → ✅ Punch-Out
- If both done → ⚠️ Attendance already completed

---

## 🗃 Database Tables

### ✅ `Logid`
Stores user login data:
- `userid` (Primary Key)
- `password`
- `name`

### ✅ `face_users`
Stores face registration status:
- `userid` (Foreign Key)
- `face_registered` (True/False)

### ✅ `attendance`
Stores attendance records:
- `userid`
- `date`
- `punch_in`
- `punch_out`
- `status`

---
