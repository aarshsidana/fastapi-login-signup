from pydantic import BaseModel, validator, Field
import re


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    mobile_number: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8)

    @validator('username')
    def validate_username(cls, v):
        # Check if empty or whitespace
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        
        v = v.strip()  # Remove leading/trailing whitespace
        
        # Check length after stripping
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username cannot be longer than 50 characters')
            
        # Only allow alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        if v.startswith('_') or v.endswith('_'):
            raise ValueError('Username cannot start or end with underscore')
        return v

    @validator('email')
    def validate_email(cls, v):
        # Check if empty or whitespace
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        
        v = v.strip().lower()  # Remove whitespace and convert to lowercase
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Please enter a valid email address')
        return v

    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        # Check if empty or whitespace
        if not v or not v.strip():
            raise ValueError('Mobile number cannot be empty')
        
        # Remove any spaces, dashes, or parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        
        if not cleaned:
            raise ValueError('Mobile number cannot be empty')
        
        # Check if it's all digits (with optional + at the start)
        if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
            raise ValueError('Mobile number must contain only digits (10-15 digits). Format: 1234567890 or +1234567890')
        return cleaned

    @validator('password')
    def validate_password(cls, v):
        # Check if empty or whitespace
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        
        # Check length
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter (A-Z)')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter (a-z)')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number (0-9)')
        
        # Check for at least one special character
        special_chars = r'[!@#$%^&*(),.?":{}|<>]'
        if not re.search(special_chars, v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)')
        
        # Check for emojis and non-ASCII characters
        if not v.isascii():
            raise ValueError('Password can only contain English letters, numbers, and special characters (no emojis)')
        
        # Additional check for common emoji patterns
        emoji_pattern = re.compile("["
                                 u"\U0001F600-\U0001F64F"  # emoticons
                                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                 u"\U0001F680-\U0001F6FF"  # transport & map
                                 u"\U0001F1E0-\U0001F1FF"  # flags
                                 "]+", flags=re.UNICODE)
        if emoji_pattern.search(v):
            raise ValueError('Password cannot contain emojis')
        
        return v


class UserLogin(BaseModel):
    username_or_email: str
    password: str

    @validator('username_or_email')
    def validate_username_or_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Username or email cannot be empty')
        return v.strip()

    @validator('password')
    def validate_password_login(cls, v):
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    mobile_number: str

    class Config:
        from_attributes = True
