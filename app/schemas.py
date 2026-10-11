# ============================================================
# schemas.py
# Purpose: Pydantic models — they define the SHAPE of data
#          going in/out of the API (validation + serialization).
# ============================================================

from pydantic import BaseModel
from datetime import datetime

# BaseModel -> Pydantic base class. Subclass it to define a schema.


class UserOut(BaseModel):
    """What we RETURN when a user is queried."""
    id: int
    name: str
    created_at: datetime

    class Config:
        # orm_mode tells Pydantic: "You can read attributes from
        # a SQLAlchemy object (not just a dict)."
        from_attributes = True   # Pydantic v2 name (v1 was orm_mode=True)


class AttendanceOut(BaseModel):
    """What we RETURN for attendance records."""
    id: int
    user_id: int
    name: str
    timestamp: datetime

    class Config:
        from_attributes = True


class RecognizeResponse(BaseModel):
    """Response from /recognize endpoint."""
    matched: bool          # did we find a match?
    name: str | None       # name if matched, else None
    user_id: int | None
    similarity: float      # cosine similarity score