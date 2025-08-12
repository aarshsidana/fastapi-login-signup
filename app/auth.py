from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas, utils


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
    # Allow login with username, email, or mobile number
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
