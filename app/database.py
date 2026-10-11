# ============================================================
# database.py
# Purpose: Set up the SQLite database connection and session.
# ============================================================

from sqlalchemy import create_engine
# create_engine -> function that creates a connection to the DB.
# Think of it as "opening a pipe" to your database file.

from sqlalchemy.orm import sessionmaker, declarative_base
# sessionmaker      -> factory that produces DB "sessions" (temporary conversations with DB).
# declarative_base  -> base class that our table models will inherit from.

# --- 1. The database URL ---
# "sqlite:///./attendance.db" means:
#   sqlite        -> use SQLite driver
#   :///          -> separator
#   ./attendance.db -> file in the current folder (auto-created if missing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./attendance.db"

# --- 2. Create the engine ---
# connect_args={"check_same_thread": False} is REQUIRED for SQLite + FastAPI
# because FastAPI handles requests in multiple threads, and SQLite by default
# blocks sharing a connection across threads. This disables that check.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# --- 3. Create a session factory ---
# Each request will open its own session (autocommit=False, autoflush=False)
# so we control when to commit changes manually.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 4. Base class ---
# Our table classes (in models.py) will inherit from Base.
# SQLAlchemy uses Base to know which classes map to DB tables.
Base = declarative_base()


# --- 5. Dependency function ---
# FastAPI uses "dependencies" to inject things (like a DB session) into routes.
# `yield` makes this a generator: code before yield runs first,
# code after yield runs when the request is done (cleanup).
def get_db():
    db = SessionLocal()      # open a session
    try:
        yield db             # give it to the route function
    finally:
        db.close()           # ALWAYS close it after, even if errors happen