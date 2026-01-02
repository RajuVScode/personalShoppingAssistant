import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "")

_engine = None
_SessionLocal = None
Base = declarative_base()

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_timeout=10,
            pool_size=3,
            max_overflow=5,
            connect_args={"connect_timeout": 5}
        )
    return _engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

engine = get_engine()
SessionLocal = get_session_local()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    try:
        with get_engine().connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
