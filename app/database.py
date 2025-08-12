import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL


Base = declarative_base()


def create_engine_with_retry(url, retries=20, delay=5):
    for attempt in range(retries):
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                pass
            print("✅ Connected to database.")
            return engine
        except OperationalError:
            print(f"⏳ DB not ready ({attempt + 1}/{retries}), retrying in {delay}s...")
            time.sleep(delay)
    raise Exception("❌ Failed to connect to database after multiple retries.")


# Don't create engine at module level
engine = None
SessionLocal = None


def get_engine():
    global engine, SessionLocal
    if engine is None:
        engine = create_engine_with_retry(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


def get_session_local():
    global SessionLocal
    if SessionLocal is None:
        get_engine()  # This will initialize both engine and SessionLocal
    return SessionLocal
