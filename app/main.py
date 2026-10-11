# ============================================================
# main.py
# Purpose: The FastAPI application — routes, request handling,
#          DB writes, and recognition logic.
# ============================================================

import json
import base64
import numpy as np
import cv2

from datetime import datetime, timedelta

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .face_engine import FaceEngine

# --- 1. Create tables at startup ---
models.Base.metadata.create_all(bind=engine)

# --- 2. Create FastAPI app ---
app = FastAPI(title="Face Attendance API")

# --- 3. Enable CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. Load face engine ONCE at startup (heavy operation) ---
engine_face = FaceEngine(model_name="buffalo_s")


# ============================================================
# STARTUP BANNER — prints URLs to terminal
# ============================================================
@app.on_event("startup")
async def show_urls():
    print("\n" + "=" * 60)
    print("  🎥  Face Attendance System — Running")
    print("=" * 60)
    print("  🏠  Home:           http://localhost:8000/")
    print("  📝  Register:       http://localhost:8000/ui/index.html")
    print("  🎥  Recognize:      http://localhost:8000/ui/recognize.html")
    print("  📋  Attendance:     http://localhost:8000/ui/attendance.html")
    print("  📚  API Docs:       http://localhost:8000/docs")
    print("  👥  Users API:      http://localhost:8000/users")
    print("  📋  Attendance API: http://localhost:8000/attendance")
    print("=" * 60)
    print("  ⚠️  Open UI via http://localhost:8000/ (NOT file://)")
    print("=" * 60 + "\n")


# ============================================================
# ROOT ROUTE — redirect to the Home landing page
# ============================================================
@app.get("/")
def root():
    """Redirect root URL to the Home landing page."""
    return RedirectResponse(url="/ui/home.html")


# ============================================================
# Helper: decode an uploaded image into an OpenCV BGR array
# ============================================================
async def read_image(file: UploadFile):
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    return img


# ============================================================
# Shared recognition logic
# ============================================================
def _run_recognition(img, db: Session):
    face = engine_face.get_largest_face(img)
    if face is None:
        return schemas.RecognizeResponse(
            matched=False, name=None, user_id=None, similarity=0.0
        )

    query_vec = face.embedding
    users = db.query(models.User).all()

    best_user = None
    best_score = -1.0
    for user in users:
        stored_vec = np.array(json.loads(user.embedding))
        score = FaceEngine.cosine_similarity(query_vec, stored_vec)
        if score > best_score:
            best_score = score
            best_user = user

    THRESHOLD = 0.4

    if best_user and best_score >= THRESHOLD:
        recent = (
            db.query(models.Attendance)
            .filter(
                models.Attendance.user_id == best_user.id,
                models.Attendance.timestamp >= datetime.utcnow() - timedelta(seconds=30)
            )
            .first()
        )
        if not recent:
            record = models.Attendance(user_id=best_user.id, name=best_user.name)
            db.add(record)
            db.commit()

        return schemas.RecognizeResponse(
            matched=True,
            name=best_user.name,
            user_id=best_user.id,
            similarity=best_score
        )

    return schemas.RecognizeResponse(
        matched=False,
        name=None,
        user_id=None,
        similarity=best_score if best_user else 0.0
    )


# ============================================================
# ROUTE 1: Register a new user
# ============================================================
@app.post("/register", response_model=schemas.UserOut)
async def register_user(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    img = await read_image(file)

    face = engine_face.get_largest_face(img)
    if face is None:
        raise HTTPException(status_code=400, detail="No face detected")

    embedding_list = face.embedding.tolist()
    embedding_json = json.dumps(embedding_list)

    user = models.User(name=name, embedding=embedding_json)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================
# ROUTE 2: Recognize (file upload)
# ============================================================
@app.post("/recognize", response_model=schemas.RecognizeResponse)
async def recognize_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    img = await read_image(file)
    return _run_recognition(img, db)


# ============================================================
# Frame schema + base64 recognition
# ============================================================
class FrameIn(BaseModel):
    image: str


@app.post("/recognize-frame", response_model=schemas.RecognizeResponse)
async def recognize_frame(
    payload: FrameIn,
    db: Session = Depends(get_db)
):
    data_url = payload.image
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(data_url)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 data")

    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    return _run_recognition(img, db)


# ============================================================
# ROUTE 3: List users
# ============================================================
@app.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# ============================================================
# ROUTE 4: List attendance
# ============================================================
@app.get("/attendance", response_model=list[schemas.AttendanceOut])
def list_attendance(db: Session = Depends(get_db)):
    return db.query(models.Attendance).order_by(models.Attendance.timestamp.desc()).all()


# ============================================================
# ROUTE 5: Delete a user
# ============================================================
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted"}


# ============================================================
# MOUNT STATIC FILES (must be at the BOTTOM, after all routes)
# ============================================================
app.mount("/ui", StaticFiles(directory="static", html=True), name="static")