# ============================================================
# camera.py
# Purpose: Local webcam loop for 20-30 FPS recognition.
# Strategy: detect every frame, but only run FULL recognition
#           every Nth frame. This keeps FPS high on CPU.
# ============================================================

import cv2
import json
import numpy as np

from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models
from .face_engine import FaceEngine


def run_camera(engine_face: FaceEngine, threshold: float = 0.4,
               recognize_every: int = 5):
    """
    engine_face     -> your already-loaded FaceEngine.
    threshold       -> similarity threshold for match.
    recognize_every -> run full recognition every N frames (5 = 6 recognitions/sec at 30 FPS).
    """

    # Open default webcam (0 = first camera).
    cap = cv2.VideoCapture(0)

    # Lower resolution = higher FPS on weak CPUs.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Cache user embeddings in memory so we don't hit DB every frame.
    db: Session = SessionLocal()
    users = db.query(models.User).all()
    db.close()

    # Pre-parse embeddings into numpy arrays once.
    user_cache = [
        (u.id, u.name, np.array(json.loads(u.embedding)))
        for u in users
    ]

    frame_count = 0
    last_result = ("Press 'q' to quit", 0.0)

    while True:
        ret, frame = cap.read()         # ret = success bool, frame = image
        if not ret:
            break

        frame_count += 1

        # --- Stage 1: Fast detection every frame ---
        face = engine_face.get_largest_face(frame)

        # --- Stage 2: Recognition every Nth frame ---
        if face is not None:
            # Draw a green rectangle around the face
            x1, y1, x2, y2 = face.bbox.astype(int)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if frame_count % recognize_every == 0 and user_cache:
                query_vec = face.embedding
                best_name = "Unknown"
                best_score = -1.0

                for uid, name, stored_vec in user_cache:
                    score = FaceEngine.cosine_similarity(query_vec, stored_vec)
                    if score > best_score:
                        best_score = score
                        best_name = name

                if best_score >= threshold:
                    last_result = (best_name, best_score)
                else:
                    last_result = ("Unknown", best_score)

        # --- Draw label above the face ---
        label, score = last_result
        cv2.putText(
            frame,
            f"{label} ({score:.2f})",
            (20, 40),                       # position (x,y)
            cv2.FONT_HERSHEY_SIMPLEX,       # font
            0.8,                            # font scale
            (0, 255, 0),                    # color (green)
            2                               # thickness
        )

        cv2.imshow("Face Attendance - press q to quit", frame)

        # waitKey(1) waits 1ms for a key press. 'q' quits.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()          # free the camera
    cv2.destroyAllWindows()


# Allow running directly: python -m app.camera
if __name__ == "__main__":
    engine = FaceEngine(model_name="buffalo_s")
    run_camera(engine)