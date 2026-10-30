# 👋 Face Attendance — User Guide

A complete, step-by-step guide to running the Face Attendance System, registering people, and checking their attendance.

---

## 📖 What This Project Does

- **Register** a person's face once via your browser webcam (stored as a 512-d face embedding — no photos saved).
- **Recognize** that person live in real time and automatically log their attendance.
- **View** attendance history with timestamps, auto-refresh, and CSV export.
- **Manage** users from a home dashboard (view, delete).
- **Optional:** Run recognition in a standalone desktop window (no browser needed).

---

## 🚀 Part 1 — Get the Project Running

### 1. Clone the repository

```bash
git clone https://github.com/BobiButt/face-attendance.git
cd face-attendance
```

### 2. Create and activate a virtual environment (recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> On first run, InsightFace will auto-download its model files (~30 MB) to `~/.insightface/models/`. This happens only once.

### 4. Start the server

```bash
python run.py
```

You should see a startup banner listing these URLs:

```
  🏠  Home:           http://localhost:8000/
  📝  Register:       http://localhost:8000/ui/index.html
  🎥  Recognize:      http://localhost:8000/ui/recognize.html
  📋  Attendance:     http://localhost:8000/ui/attendance.html
  📚  API Docs:       http://localhost:8000/docs
```

Keep that terminal running while you use the app.

### 5. Open in your browser

Go to: **http://localhost:8000/**

> ⚠️ **Important:** Open the app through `http://localhost:8000`. Do **not** open the HTML files directly (`file://`), or the browser will block webcam access for security.

---

## 👤 Part 2 — Register a User (Capture Their Face)

1. Go to **http://localhost:8000/ui/index.html** (or click **Register** on the home page).
2. Click **▶ Start Camera** and allow camera permission when prompted.
3. Type the person's name in the name box.
4. Position your face in the camera frame, then click **📸 Capture**. A preview appears.
5. Click **✅ Register User**.

The system detects the largest face, extracts a 512-d face embedding, and stores only the embedding + name in the SQLite database. **No raw photo is saved.**

You'll see a confirmation like: `User "John Doe" registered (ID: 1)`.


## 🎥 Part 3 — Check Attendance / Recognize a Face Live

1. Go to **http://localhost:8000/ui/recognize.html** (or click **Recognize** on the home page).
2. Click **▶ Start Recognition**.
3. Show your face to the webcam.

Within ~1.5 seconds, the overlay shows:

| Result | Meaning |
|--------|---------|
| ✅ Name (green) | You're recognized — attendance is logged automatically |
| ❓ Unknown person (red) | Face detected but not in the database |
| 👀 No face detected (gray) | No face in frame |

### What happens behind the scenes

- Every 1.5s the browser sends a webcam frame to `/recognize-frame`.
- The server compares the face against all registered embeddings using cosine similarity.
- If similarity ≥ 0.4, it's a match.
- An attendance record is created **only once per 30 seconds** per person (to avoid duplicate check-ins if you keep standing in front of the camera).

---

## 📋 Part 4 — View Attendance History

1. Go to **http://localhost:8000/ui/attendance.html** (or click **Attendance** on the home page).
2. You'll see a table with every check-in: ID, User ID, Name, Timestamp.
3. The list auto-refreshes every 5 seconds (toggle with the **Auto-refresh** checkbox).
4. Click **🔄 Refresh** to reload manually.
5. Click **⬇ CSV** to download all attendance records as a CSV file (`attendance_YYYY-MM-DD.csv`).

---

## 🏠 Part 5 — Home Dashboard

Go to **http://localhost:8000/** to see:

- Total registered users
- Total attendance records
- Today's attendance count
- Server status indicator
- A list of all registered users with a **🗑 Delete** button next to each
- Quick CTA buttons to go to Register or Recognize

Stats auto-refresh every 5 seconds.

---

## 🖥️ Part 6 — Desktop Camera Mode (No Browser)

If you don't want to use the browser, there's a standalone OpenCV script:

```bash
python -m app.camera
```

A window opens showing your webcam:
- 🟢 Green box around the detected face
- 📛 Name + similarity score (e.g. `John Doe (0.87)`) or `Unknown`
- Press **`q`** to quit

Edit `app/camera.py` to adjust:
- `threshold=0.4` — higher = stricter matching (fewer false positives)
- `recognize_every=5` — run full recognition every N frames (lower = more frequent, more CPU)

---

## 🔌 Part 7 — Quick API Reference

The app also exposes a REST API (Swagger docs at **http://localhost:8000/docs**):

| Method | Endpoint | What it does |
|--------|----------|--------------|
| POST | `/register` | Register a user (`name` + `file` image) |
| POST | `/recognize` | Recognize a face from an uploaded image |
| POST | `/recognize-frame` | Recognize a base64-encoded frame (used by the browser UI) |
| GET | `/users` | List all registered users |
| GET | `/attendance` | List attendance records (newest first) |
| DELETE | `/users/{user_id}` | Delete a user |

Example — register via curl:

```bash
curl -X POST http://localhost:8000/register \
  -F "name=John Doe" \
  -F "file=@john.jpg"
```

Example — recognize via curl:

```bash
curl -X POST http://localhost:8000/recognize \
  -F "file=@test.jpg"
```

---

## ⚠️ Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| Camera doesn't start | Open via `http://localhost:8000`, not `file://` |
| "Camera API not available" | Use Chrome, Edge, or Firefox (not Internet Explorer) |
| "Permission denied" | Click the 🔒 icon in the URL bar → Allow camera |
| "NotReadableError" | Another app (Zoom/Teams/OBS) is using the camera — close it |
| "No face detected" on register | Move closer to camera, better lighting, face forward |
| `ModuleNotFoundError: app` | Run `python run.py` from the project root folder |
| Port 8000 already in use | Change the port in `run.py` |
| InsightFace re-downloads models | Make sure `~/.insightface/models/` exists |

---

## 🗂️ Where Data Is Stored

- **Database:** `attendance.db` (SQLite) — created automatically in the project folder on first run.
- **Models:** `~/.insightface/models/` — downloaded automatically by InsightFace on first run.
- **No photos are saved** — only names and 512-d numeric embeddings.

---

## ✅ Quick Summary Checklist

1. `git clone ...` → `cd face-attendance`
2. `python -m venv venv` → activate
3. `pip install -r requirements.txt`
4. `python run.py`
5. Open **http://localhost:8000/**
6. Register a face at `/ui/index.html`
7. Recognize at `/ui/recognize.html` (attendance logs automatically)
8. View history at `/ui/attendance.html` → export CSV if needed

---

*Built with FastAPI + InsightFace + OpenCV + SQLite. Maintained by Mubeen (@BobiButt).*
> 💡 Tips: Face the camera directly, use good lighting, and make sure your face is clearly visible and not too far away.