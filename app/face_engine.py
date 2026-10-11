# ============================================================
# face_engine.py
# Purpose: Load InsightFace, detect faces, extract embeddings,
#          and compare embeddings for recognition.
# ============================================================

import numpy as np
# numpy -> fast array math (embeddings are vectors).

import insightface
from insightface.app import FaceAnalysis
# FaceAnalysis -> high-level wrapper that runs detection + embedding
#                 using the downloaded ONNX models.


class FaceEngine:
    """
    Wraps InsightFace so the rest of the code doesn't care about details.
    """

    def __init__(self, model_name: str = "buffalo_s"):
        """
        __init__ -> the constructor. Runs once when you do FaceEngine().

        model_name choices:
          'buffalo_s' -> small + fast (recommended for low-end CPU)
          'buffalo_l' -> large + accurate (slower)
        """
        # FaceAnalysis downloads/loads models into memory.
        # providers=['CPUExecutionProvider'] forces CPU (skip GPU).
        self.app = FaceAnalysis(
            name=model_name,
            providers=['CPUExecutionProvider']
        )

        # prepare() loads the actual ONNX files and warms them up.
        # ctx_id=-1 -> use CPU (0 would be GPU 0).
        # det_size=(320, 320) -> smaller detection input = faster on CPU.
        #                        Use (640,640) for better accuracy if you can afford it.
        self.app.prepare(ctx_id=-1, det_size=(320, 320))

    # ---------------------------------------------------------
    def get_faces(self, img_bgr):
        """
        Detect all faces in an image and return their data.
        
        img_bgr -> image in OpenCV BGR format (numpy array).
        Returns: list of Face objects, each with:
            .bbox        -> bounding box [x1,y1,x2,y2]
            .embedding   -> 512-d numpy vector
            .det_score   -> detection confidence
        """
        faces = self.app.get(img_bgr)
        return faces

    # ---------------------------------------------------------
    def get_largest_face(self, img_bgr):
        """
        Convenience: pick the LARGEST face in the frame
        (usually the person closest to the camera).
        Returns: Face object or None if no face found.
        """
        faces = self.get_faces(img_bgr)
        if not faces:
            return None

        # Sort by area of bounding box, biggest first.
        faces.sort(
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
            reverse=True
        )
        return faces[0]

    # ---------------------------------------------------------
    @staticmethod
    def cosine_similarity(a, b):
        """
        Measure how similar two vectors are.
        Result range: -1 (opposite) to 1 (identical).
        For face embeddings, > 0.4 usually means "same person".

        @staticmethod -> doesn't need `self`; call as FaceEngine.cosine_similarity(a,b)
        """
        a = a / np.linalg.norm(a)   # normalize to unit length
        b = b / np.linalg.norm(b)
        return float(np.dot(a, b))  # dot product of unit vectors = cosine