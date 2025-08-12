from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from . import database, models, schemas, auth
from .database import Base
from datetime import datetime, timedelta
from .config import ACCESS_TOKEN_EXPIRE_MINUTES
import re


app = FastAPI(title="FastAPI Authentication System", version="1.0.0")
security = HTTPBearer()


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


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db)
):
    """Dependency to get current user from JWT token"""
    token = credentials.credentials
    user = auth.get_current_user(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_device_info(request: Request) -> str:
    """Extract device information from request"""
    user_agent = request.headers.get("user-agent", "Unknown")
    browser_match = re.search(r'(Chrome|Firefox|Safari|Edge|Opera)/[\d.]+', user_agent)
    browser = browser_match.group(0) if browser_match else "Unknown Browser"
    return f"{browser} - {user_agent[:100]}"


def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "Unknown"


@app.post("/register", response_model=schemas.TokenResponse)
def register(user: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    try:
        ensure_tables_created()
        
        # Register user
        db_user = auth.register_user(db, user)
        
        # Create access token
        token_data = {
            "sub": str(db_user.id),  # Convert to string for JWT
            "username": db_user.username
        }
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, jti = auth.create_access_token(
            data=token_data, 
            expires_delta=access_token_expires
        )
        
        # Create user session with device info
        device_info = get_device_info(request)
        ip_address = get_client_ip(request)
        auth.create_user_session(db, db_user.id, jti, device_info, ip_address)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "mobile_number": db_user.mobile_number,
                "created_at": db_user.created_at if hasattr(db_user, 'created_at') else datetime.utcnow()
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/login", response_model=schemas.TokenResponse)
def login(user: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    try:
        ensure_tables_created()
        
        # Authenticate user
        user_obj = auth.authenticate_user(db, user.username_or_email, user.password)
        if not user_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        token_data = {
            "sub": str(user_obj.id),  # Convert to string for JWT
            "username": user_obj.username
        }
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, jti = auth.create_access_token(
            data=token_data, 
            expires_delta=access_token_expires
        )
        
        # Create user session (handles 2-device limit automatically)
        device_info = get_device_info(request)
        ip_address = get_client_ip(request)
        auth.create_user_session(db, user_obj.id, jti, device_info, ip_address)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user_obj.id,
                "username": user_obj.username,
                "email": user_obj.email,
                "mobile_number": user_obj.mobile_number,
                "created_at": user_obj.created_at if hasattr(user_obj, 'created_at') else datetime.utcnow()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# Add new endpoint to view active sessions
@app.get("/sessions")
def get_active_sessions(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's active sessions"""
    try:
        sessions = auth.get_user_active_sessions(db, current_user.id)
        
        session_info = []
        for session in sessions:
            session_info.append({
                "device_info": session.device_info,
                "ip_address": session.ip_address,
                "created_at": session.created_at,
                "last_active": session.last_active,
                "is_current": False  # You could add logic to detect current session
            })
        
        return {
            "user": current_user.username,
            "active_sessions": session_info,
            "session_count": len(session_info),
            "max_sessions": 2
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout user by blacklisting token"""
    try:
        token = credentials.credentials
        token_data = auth.verify_token(token, db)
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Blacklist the token
        jti = token_data.get("jti")
        user_id = token_data.get("user_id")
        
        if jti and user_id:
            success = auth.logout_user(db, jti, user_id)
            if not success:
                raise HTTPException(status_code=500, detail="Logout failed")
        
        return {
            "message": "Successfully logged out.",
            "logged_out_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/profile", response_model=schemas.UserOut)
def get_profile(current_user: models.User = Depends(get_current_user)):
    """Get user profile"""
    try:
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "mobile_number": current_user.mobile_number,
            "created_at": current_user.created_at if hasattr(current_user, 'created_at') else datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/verify-token")
def verify_token(current_user: models.User = Depends(get_current_user)):
    """Verify if token is valid"""
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "message": "Token is valid"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


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
            "example": "+1234567890 or +91234567890"
        },
        "token": {
            "expires_in": f"{ACCESS_TOKEN_EXPIRE_MINUTES} minutes (7 days)",
            "type": "Bearer JWT",
            "blacklisting": "Tokens are invalidated on logout"
        }
    }
