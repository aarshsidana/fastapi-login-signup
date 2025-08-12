from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import database, models, schemas, auth
from .database import Base


app = FastAPI()


def get_db():
    SessionLocal = database.get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_tables_created():
    """Create tables on first database access"""
    try:
        engine = database.get_engine()
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise


@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        ensure_tables_created()
        return auth.register_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    try:
        ensure_tables_created()
        user_obj = auth.authenticate_user(db, user.username_or_email, user.password)
        if not user_obj:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {
            "message": "Login successful!", 
            "user": {
                "id": user_obj.id,
                "username": user_obj.username,
                "email": user_obj.email,
                "mobile_number": user_obj.mobile_number
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/validation-rules")
def get_validation_rules():
    return {
        "username": {
            "min_length": 3,
            "max_length": 50,
            "allowed_chars": "letters, numbers, underscores only",
            "restrictions": "cannot start or end with underscore"
        },
        "password": {
            "min_length": 8,
            "requirements": [
                "At least 1 uppercase letter",
                "At least 1 lowercase letter", 
                "At least 1 digit",
                "At least 1 special character (!@#$%^&*(),.?\":{}|<>)",
                "ASCII characters only (no emojis or special language characters)"
            ]
        },
        "mobile_number": {
            "format": "10-15 digits",
            "example": "+1234567890 or 9876543210"
        }
    }
