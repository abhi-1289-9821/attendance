# Smart Face Recognition Attendance System

A production-ready AI-powered attendance management platform that automates classroom attendance using Face Recognition, Flask Web Application, MySQL Database, and OpenCV.

This system eliminates manual attendance, prevents proxy entries, and provides real-time subject-wise attendance analytics through a secure student dashboard.

---

# Overview

Traditional attendance systems are slow, error-prone, and easy to manipulate. This project modernizes attendance management by using real-time face recognition at classroom entry points.

Students register through a web portal, capture their face once, and later attendance is marked automatically when recognized by the camera system.

---

# Key Features

## Student Portal
- Student Registration with Face Capture
- Secure Login System
- Dashboard with Attendance Percentage
- Subject-wise Attendance Report

## Face Recognition Engine
- Real-time webcam recognition
- Face encoding storage
- High accuracy student identification
- Automated attendance updates

## Smart Attendance Logic
- Entry / Exit based detection
- Multiple scans supported
- Minimum stay duration required
- Prevents false attendance marking

## Database Management
- Student records
- User login credentials
- Subject data
- Timetable
- Attendance logs

---

# Tech Stack

| Layer | Technology |
|------|------------|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python Flask |
| AI Engine | OpenCV, face_recognition |
| Database | MySQL |
| Authentication | Session Based Login |
| Storage | encodings.pkl |

---

# System Architecture

```text
Student Registration Portal
        ↓
Capture Face Image
        ↓
Generate Face Encoding
        ↓
Store in Database + encodings.pkl
        ↓
Door Camera Recognition
        ↓
Attendance Logic Engine
        ↓
MySQL Update
        ↓
Student Dashboard
