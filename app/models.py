# ============================================================
# models.py
# Purpose: Define the database TABLES as Python classes.
# ============================================================

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
# Column        -> represents a table column.
# Integer, String, Float, DateTime, Text -> column data types.

from datetime import datetime
# For auto-timestamping attendance records.

from .database import Base
# Import our Base class so tables register with SQLAlchemy.


class User(Base):
    """
    User table: one row per REGISTERED person.
    """
    __tablename__ = "users"   # actual table name in SQLite

    id = Column(Integer, primary_key=True, index=True)
    # primary_key=True -> unique auto-increment ID.
    # index=True       -> creates an index (fast lookups).

    name = Column(String, nullable=False)
    # nullable=False -> this column cannot be empty.

    embedding = Column(Text, nullable=False)
    # We store the face embedding (list of 512 floats) as a JSON STRING.
    # SQLite has no native array type, so Text + JSON is the standard trick.

    created_at = Column(DateTime, default=datetime.utcnow)
    # default -> auto-fill with current UTC time when a row is created.


class Attendance(Base):
    """
    Attendance table: one row every time a known face is recognized.
    """
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # which user was recognized
    name = Column(String, nullable=False)      # duplicated for easy reading
    timestamp = Column(DateTime, default=datetime.utcnow)