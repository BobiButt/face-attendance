# ⚙️ How Face Attendance Works

A technical overview of what the project does, how it stores data, what every package does, and the full step-by-step working procedure.

---

## 1. What This Project Does

Face Attendance is a **real-time face recognition attendance system**. It lets you:

1. **Register a person once** by capturing their face through a browser webcam.
2. **Recognize that person live** in front of the webcam.
3. **Automatically log attendance** when a known face is recognized.
4. **View, auto-refresh, and export** attendance history to CSV.
5. **Manage users** (list + delete) from a home dashboard.
6. Optionally run recognition in a **standalone desktop window** (`app/camera.py`) without a browser.

---

## 2. Packages Used & Their Purpose

All packages are listed in `requirements.txt`. Below is each one and exactly what it does in this project.

| Package | Purpose in This Project |
|---------|------------------------|
| **fastapi** | The web framework. Defines all API routes (`/register`, `/recognize`, `/users`, etc.), handles requests/responses, and serves the static HTML UI. |
| **uvicorn[standard]** | The ASGI server that runs the FastAPI app. `python run.py` starts uvicorn on `http://localhost:8000`. |
| **opencv-python** (`cv2`) | Image processing. Used to decode uploaded images, grab webcam frames, draw detection boxes/labels, and run the standalone desktop camera script. |
| **insightface** | The face AI library. Provides `FaceAnalysis` which performs **face detection** and **512-d embedding extraction** (using the buffalo_s / MobileFaceNet ONNX models). |
| **onnxruntime** | The runtime that executes InsightFace's ONNX models on CPU. Required for the face detection + embedding models to actually run. |
| **sqlalchemy** | The database ORM. Defines the `User` and `Attendance` tables, manages the SQLite connection, sessions, and queries. |
| **pydantic** | Data validation and serialization. Defines the shapes of API requests/responses (`UserOut`, `AttendanceOut`, `RecognizeResponse`) and converts SQLAlchemy objects to JSON. |
| **numpy** | Numerical array math. Used to handle face embeddings (512-d vectors), compute cosine similarity, and manipulate image arrays. |
| **python-multipart** | Enables FastAPI to parse `multipart/form-data`, which is used when uploading an image file (`file`) together with a text name (`name`) during registration. |

### Standard-library modules also used
- `json` — serialize/deserialize embeddings to/from JSON strings for SQLite storage.
- `base64` — decode base64-encoded webcam frames sent from the browser.
- `datetime`, `timedelta` — timestamps for attendance records and the 30-second deduplication window.
- `cv2` (from opencv-python) — camera access and image drawing.

---

## 3. How Data Is Stored (Images vs. Embeddings)

### ❌ No raw photos are stored
The project **does not save any image files** (no `.jpg`, `.png`, etc.). When you register, the captured photo is used only momentarily to compute a face embedding, then discarded.

### ✅ Only 512-d face embeddings are stored
Each registered person is stored as one row in the `users` table:

| Column | Type | What it holds |
|--------|------|---------------|
| `id` | Integer (PK) | Auto-increment user ID |
| `name` | Text | Person's name |
| `embedding` | Text (JSON string) | The 512-d face embedding, serialized as JSON |
| `created_at` | DateTime | When the user was registered |

The `embedding` column holds a JSON array of 512 floating-point numbers — a mathematical "fingerprint" of the face. It cannot be reversed back into a photo, which makes the system privacy-first.

Attendance records live in a separate `attendance` table:

| Column | Type | What it holds |
|--------|------|---------------|
| `id` | Integer (PK) | Auto-increment record ID |
| `user_id` | Integer | Which user was recognized |
| `name` | Text | Duplicated name for easy reading |
| `timestamp` | DateTime | When the check-in happened |

The database file is `attendance.db` (SQLite), created automatically in the project root on first run.

---

## 4. Full Working Procedure (Step by Step)

### Step 1 — Start the server
```
python run.py
```
This launches Uvicorn, which loads `app.main:app`. At startup it:
- Creates the SQLite tables (`users`, `attendance`) if they don't exist.
- Loads the InsightFace `FaceEngine` once into memory (loads the buffalo_s ONNX models).
- Mounts the `static/` folder at `/ui` so the browser pages are served.

### Step 2 — Register a face (browser UI)
1. User opens `http://localhost:8000/ui/index.html`.
2. Starts the webcam, enters a name, and clicks **Capture**.
3. The browser sends a `multipart/form-data` POST to `/register` with fields `name` and `file`.
4. `main.py` decodes the image, runs `engine_face.get_largest_face(img)` to detect the face and extract its 512-d embedding.
5. The embedding is converted to a Python list, serialized to JSON, and saved as a new `User` row in SQLite.
6. The user is now registered and can be recognized later.

### Step 3 — Live recognition (browser UI)
1. User opens `http://localhost:8000/ui/recognize.html`.
2. Starts the webcam. Every ~1.5s, `recognizeLoop()` grabs a frame, converts it to a base64 JPEG, and POSTs it to `/recognize-frame`.
3. `main.py` decodes the base64 back to an image, runs `get_largest_face()` to extract the query embedding.
4. It fetches **all** registered users from SQLite, parses each stored JSON embedding back into a numpy vector, and computes **cosine similarity** between the query embedding and every stored embedding.
5. If the best similarity ≥ `THRESHOLD` (default `0.4`), it's a match.

### Step 4 — Attendance logging (30-second deduplication)
When a match is found, `main.py` checks the `attendance` table for any record from the same user within the last 30 seconds:
- If **no recent record** exists → inserts a new `Attendance` row (`user_id`, `name`, `timestamp`).
- If a recent record **does exist** → skips logging (prevents duplicate check-ins while someone stands still in front of the camera).
6. The server returns a `RecognizeResponse` (`matched`, `name`, `user_id`, `similarity`) which the browser displays as ✅ Name / ❓ Unknown / 👀 No face.

### Step 5 — View and export attendance
1. User opens `http://localhost:8000/ui/attendance.html`.
2. The page fetches `GET /attendance` (records sorted newest first) and renders a table.
3. Auto-refresh reloads every 5 seconds (toggleable).
4. Clicking **⬇ CSV** builds a CSV string from the last fetched data and triggers a browser download (`attendance_YYYY-MM-DD.csv`).


---

## 5. File-by-File Breakdown

| File | Role |
|------|------|
| `run.py` | Entry point. Starts `uvicorn.run("app.main:app", ...)` on port 8000 with auto-reload. |
| `app/main.py` | Core logic. FastAPI app, all routes (`/register`, `/recognize`, `/recognize-frame`, `/users`, `/attendance`, `DELETE /users/{user_id}`), image decoding, recognition engine, 30-second dedup, static file mounting. |
| `app/database.py` | SQLite engine, session factory (`SessionLocal`), base class, and `get_db()` dependency for FastAPI. |
| `app/models.py` | SQLAlchemy table definitions: `User` and `Attendance`. |
| `app/schemas.py` | Pydantic response schemas: `UserOut`, `AttendanceOut`, `RecognizeResponse`. |
| `app/face_engine.py` | Wraps InsightFace. `FaceEngine` class loads the model, detects faces (`get_faces`), picks the largest face (`get_largest_face`), and provides a static `cosine_similarity()` helper. |
| `app/camera.py` | Standalone OpenCV desktop script (`python -m app.camera`). Runs detection every frame and full recognition every Nth frame in a local window (no browser). |
| `static/index.html` | Register page: webcam capture + name input + register. |
| `static/recognize.html` | Recognize page: live webcam recognition overlay. |
| `static/attendance.html` | Attendance page: history table, auto-refresh, CSV export. |
| `static/home.html` | Dashboard: stats, user list, delete users, quick links. |
| `requirements.txt` | All Python package dependencies (listed in Section 2 above). |

---

## 6. Recognition Flow (Text Diagram)

```
Registration:
[Webcam Photo] → Face Detection → 512-d Embedding → JSON → SQLite (users table)

Recognition:
[Webcam Frame] → Face Detection → Query Embedding
                                    ↓
                          Compare with ALL stored embeddings
                                    ↓
                          Cosine similarity ≥ 0.4?
                                    ↓
                          Yes → Check 30-sec dedup → Log Attendance → Return Name
                          No  → Return "Unknown"
```

---

## 7. Quick Reference: Key Constants

| Constant | File | Default | Meaning |
|----------|------|---------|---------|
| `THRESHOLD` | `app/main.py` | `0.4` | Minimum cosine similarity to count as a match (higher = stricter). |
| Deduplication window | `app/main.py` | `30 seconds` | Ignore repeat check-ins from the same user within this window. |
| Recognition interval (desktop) | `app/camera.py` | `every 5 frames` | Run full embedding comparison every N frames to keep FPS high. |
| Detection input size | `app/face_engine.py` | `(320, 320)` | Smaller = faster on CPU; `(640, 640)` for better accuracy. |

---

*This document covers the working procedure, data storage, and purpose of every package used in the Face Attendance project.*
