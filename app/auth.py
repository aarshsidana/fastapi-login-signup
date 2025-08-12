from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from . import models, schemas, utils
from datetime import datetime, timedelta
from jose import JWTError, jwt
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import uuid


def register_user(db: Session, user: schemas.UserCreate):
    # Check if username, email, or mobile already exists
    existing_user = db.query(models.User).filter(
        or_(
            models.User.username == user.username,
            models.User.email == user.email,
            models.User.mobile_number == user.mobile_number
        )
    ).first()
    
    if existing_user:
        if existing_user.username == user.username:
            raise ValueError("Username already registered")
        if existing_user.email == user.email:
            raise ValueError("Email already registered")
        if existing_user.mobile_number == user.mobile_number:
            raise ValueError("Mobile number already registered")
    
    hashed_pw = utils.hash_password(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        mobile_number=user.mobile_number,
        hashed_password=hashed_pw
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username_or_email: str, password: str):
    user = db.query(models.User).filter(
        or_(
            models.User.username == username_or_email,
            models.User.email == username_or_email,
            models.User.mobile_number == username_or_email
        )
    ).first()
    
    if not user or not utils.verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add JWT ID for blacklisting and session management
    jti = str(uuid.uuid4())
    
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti


def is_token_blacklisted(db: Session, jti: str) -> bool:
    """Check if token is blacklisted"""
    try:
        blacklisted = db.query(models.TokenBlacklist).filter(
            models.TokenBlacklist.jti == jti
        ).first()
        return blacklisted is not None
    except Exception:
        return False


def blacklist_token(db: Session, jti: str, user_id: int):
    """Add token to blacklist"""
    try:
        # Check if already blacklisted
        if is_token_blacklisted(db, jti):
            return True
        
        blacklist_entry = models.TokenBlacklist(
            jti=jti,
            user_id=user_id
        )
        db.add(blacklist_entry)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def create_user_session(db: Session, user_id: int, jti: str, device_info: str = None, ip_address: str = None):
    """Create new user session and manage 2-device limit"""
    try:
        # Check active sessions count
        active_sessions = db.query(models.UserSession).filter(
            and_(
                models.UserSession.user_id == user_id,
                models.UserSession.is_active == True
            )
        ).count()
        
        # If user has 2 or more active sessions, deactivate the oldest one
        if active_sessions >= 2:
            oldest_session = db.query(models.UserSession).filter(
                and_(
                    models.UserSession.user_id == user_id,
                    models.UserSession.is_active == True
                )
            ).order_by(models.UserSession.last_active.asc()).first()
            
            if oldest_session:
                # Blacklist the oldest session token
                blacklist_token(db, oldest_session.jti, user_id)
                
                # Deactivate session
                oldest_session.is_active = False
                db.commit()
        
        # Create new session
        new_session = models.UserSession(
            user_id=user_id,
            jti=jti,
            device_info=device_info,
            ip_address=ip_address,
            is_active=True
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
        
    except Exception:
        db.rollback()
        return None


def verify_token(token: str, db: Session = None):
    """Verify JWT token and check blacklist"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")  # JWT subject is string
        username: str = payload.get("username")
        jti: str = payload.get("jti")
        
        if user_id_str is None or username is None or jti is None:
            return None
        
        # Convert string back to integer for database queries
        try:
            user_id = int(user_id_str)
        except ValueError:
            return None
        
        # Check if token is blacklisted
        if db and is_token_blacklisted(db, jti):
            return None
        
        # Update session last active time
        if db:
            session = db.query(models.UserSession).filter(
                and_(
                    models.UserSession.jti == jti,
                    models.UserSession.is_active == True
                )
            ).first()
            
            if session:
                session.last_active = datetime.utcnow()
                db.commit()
        
        return {"user_id": user_id, "username": username, "jti": jti}
        
    except JWTError:
        return None
    except Exception:
        return None


def get_current_user(db: Session, token: str):
    """Get current user from token"""
    try:
        token_data = verify_token(token, db)
        if token_data is None:
            return None
        
        user_id = token_data["user_id"]
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return user
        
    except Exception:
        return None


def logout_user(db: Session, jti: str, user_id: int):
    """Logout user by blacklisting token and deactivating session"""
    try:
        # Blacklist the token
        blacklist_success = blacklist_token(db, jti, user_id)
        
        # Deactivate session
        session = db.query(models.UserSession).filter(
            models.UserSession.jti == jti
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
        
        return blacklist_success
        
    except Exception:
        db.rollback()
        return False


def get_user_active_sessions(db: Session, user_id: int):
    """Get user's active sessions"""
    try:
        sessions = db.query(models.UserSession).filter(
            and_(
                models.UserSession.user_id == user_id,
                models.UserSession.is_active == True
            )
        ).order_by(models.UserSession.last_active.desc()).all()
        
        return sessions
    except Exception:
        return []
