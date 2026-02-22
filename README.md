# 🎓 LPU SmartAttend — AI-Powered Campus Attendance System

## 🚀 Quick Start (VSCode)

```bash
# 1. Open folder in VSCode, open terminal

# 2. Install everything
pip install -r requirements.txt

# 3. Setup database
python manage.py makemigrations accounts attendance
python manage.py migrate

# 4. Load demo data
python manage.py seed_data

# 5. Run server
python manage.py runserver
```

Open: **http://127.0.0.1:8000**

---

## 🔐 Login Credentials

| Role | Username | Password |
|------|----------|----------|
| HOD (Admin) | `hod` | `hod123` |
| Faculty | `faculty1` | `fac123` |

---

## 👥 Role System

### 🏛️ HOD (Head of Department)
- Add/Edit faculty members with login credentials
- Manage departments and courses
- View all attendance reports
- Monitor all faculty and students

### 👨‍🏫 Faculty
- Create attendance sessions (Manual / Face AI / Both)
- Mark attendance manually (one-click per student)
- Use DeepFace AI face recognition (webcam or photo upload)
- View session reports

### 🎓 Students
- View their own attendance percentages
- See course-wise breakdown
- Receive absence notifications

---

## 🤖 Face Recognition (DeepFace)

### How to enroll a student:
1. Faculty goes to **Add Student**
2. Click **"Start Camera"** → webcam opens
3. Click **"Capture"** → face is saved
4. Or upload an existing clear photo

### How face attendance works:
1. Faculty creates a session → selects **"Face Recognition"** mode
2. On the face attendance page, click **"Start Camera"**
3. Click **"Scan Faces Now"** → DeepFace analyzes frame
4. Recognized students auto-marked ✅ Present
5. Or upload a classroom photo → bulk recognition
6. Click **"Finalize & Save"** to close session

---

## 📁 Project Structure

```
lpu_smart/
├── manage.py
├── requirements.txt
├── setup_and_run.bat
├── core/                  ← Django project config
├── accounts/              ← HOD, Faculty, Student models & views
├── attendance/            ← Sessions, Records, Face Recognition
│   └── face_utils.py      ← DeepFace integration
└── templates/
    ├── base.html          ← Dark modern sidebar UI
    ├── accounts/          ← Login, Dashboard, Student/Faculty pages
    └── attendance/        ← Session, Face AI, Reports pages
```

---

## ⚠️ DeepFace Note

DeepFace requires heavy dependencies (`tensorflow`, `keras`). First recognition will be **slow** (model download ~500MB). Subsequent ones are faster.

If DeepFace install fails:
```bash
pip install deepface tf-keras opencv-python
```
# AI-based_smart_attendance_system
