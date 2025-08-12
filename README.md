# FastAPI JWT Authentication System

A comprehensive user authentication system built with FastAPI, MySQL, and Docker. Features JWT token authentication, session management, device limits, and robust security measures.

## 🚀 Features

### Core Authentication
- ✅ **User Registration** with comprehensive validation
- ✅ **User Login** with JWT token generation
- ✅ **Token-based Logout** with blacklisting
- ✅ **Multi-login Support** - Login with username, email, or mobile number
- ✅ **7-day JWT Token Expiry** (configurable)

### Security Features
- 🔒 **Password Encryption** using bcrypt
- 🛡️ **JWT Token Security** with blacklisting on logout
- 🚫 **SQL Injection Protection** via SQLAlchemy ORM
- ⚠️ **Input Validation** and sanitization
- 🔐 **Token Expiration** and refresh mechanisms

### Session Management
- 📱 **2-Device Login Limit** - Automatic logout of oldest session
- 💾 **Session Tracking** with device info and IP addresses
- 🕒 **Last Active Tracking** for each session
- 📊 **Active Sessions View** for users

### Data Validation
- **Username**: 3-50 characters, alphanumeric + underscores only
- **Email**: Proper email format validation with uniqueness check
- **Mobile**: 10-15 digits, international format supported
- **Password**: 8+ characters with complexity requirements:
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
  - At least 1 special character
  - No emojis or non-ASCII characters

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: Passlib with bcrypt
- **Validation**: Pydantic
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose installed
- Git (for cloning)
- Python 3.11+ (for local development)

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/aarshsidana/fastapi-auth-backend.git
   cd fastapi-auth-backend
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration if needed
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Validation Rules: http://localhost:8000/validation-rules

## ⚙️ Environment Configuration

Create a `.env` file in the root directory:

```env
# Database Configuration
DB_USER=fastapi_user
DB_PASSWORD=Devil@123
DB_HOST=db
DB_NAME=auth_db

# JWT Configuration
SECRET_KEY=your_super_secret_key_here_make_it_long_and_random_at_least_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days
```

## 📚 API Documentation

### 🔐 Authentication Endpoints

#### POST /register
Register a new user and receive JWT token

**Request Body:**
```json
{
  "username": "john_doe123",
  "email": "john@example.com",
  "mobile_number": "1234567890",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": 1,
    "username": "john_doe123",
    "email": "john@example.com",
    "mobile_number": "1234567890",
    "created_at": "2025-08-12T15:30:00Z"
  }
}
```

#### POST /login
Login with username, email, or mobile number

**Request Body:**
```json
{
  "username_or_email": "john_doe123",
  "password": "SecurePass123!"
}
```

**Response:** Same as registration

#### POST /logout
Logout and invalidate current token

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "message": "Successfully logged out. Token has been invalidated.",
  "logged_out_at": "2025-08-12T15:35:00Z"
}
```

### 👤 User Endpoints

#### GET /profile
Get user profile information

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe123",
  "email": "john@example.com",
  "mobile_number": "1234567890",
  "created_at": "2025-08-12T15:30:00Z"
}
```

#### GET /sessions
View active user sessions

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "user": "john_doe123",
  "active_sessions": [
    {
      "device_info": "Chrome/91.0 - Mozilla/5.0...",
      "ip_address": "192.168.1.100",
      "created_at": "2025-08-12T15:30:00Z",
      "last_active": "2025-08-12T15:35:00Z",
      "is_current": false
    }
  ],
  "session_count": 1,
  "max_sessions": 2
}
```

### 🔧 Utility Endpoints

#### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-12T15:30:00Z"
}
```

#### GET /verify-token
Verify if current token is valid

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "valid": true,
  "user_id": 1,
  "username": "john_doe123",
  "message": "Token is valid"
}
```

#### GET /validation-rules
Get validation requirements for all fields

**Response:** Returns detailed validation rules for username, password, email, mobile number, and token information.

## 🗂️ Project Structure

```
fastapi-auth-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and endpoints
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic validation schemas
│   ├── auth.py              # Authentication logic
│   ├── utils.py             # Password hashing utilities
│   ├── database.py          # Database connection setup
│   └── config.py            # Configuration management
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template
├── .gitignore               # Git ignore file
├── docker-compose.yml       # Docker compose configuration
├── Dockerfile               # Docker container setup
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

## 💾 Database Schema

### Users Table
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)  
- `mobile_number` (Unique)
- `hashed_password`
- `created_at`

### Token Blacklist Table
- `id` (Primary Key)
- `jti` (JWT ID - Unique)
- `user_id`
- `blacklisted_at`

### User Sessions Table
- `id` (Primary Key)
- `user_id`
- `jti` (JWT ID - Unique)
- `device_info`
- `ip_address`
- `is_active`
- `created_at`
- `last_active`

## 🔄 Session Management Logic

1. **Registration/Login**: Creates new session with device info
2. **Device Limit**: Maximum 2 active sessions per user
3. **Auto Logout**: Oldest session deactivated when limit exceeded
4. **Token Tracking**: Each token linked to a specific session
5. **Logout**: Blacklists token and deactivates session

## 🧪 Testing

### Manual Testing with Swagger UI
1. Visit `http://localhost:8000/docs`
2. Use the interactive API documentation
3. Test all endpoints with real data

### Manual Testing with curl

**Register:**
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser123",
    "email": "test@example.com",
    "mobile_number": "1234567890",
    "password": "TestPass123!"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "testuser123",
    "password": "TestPass123!"
  }'
```

**Access Profile:**
```bash
curl -X GET "http://localhost:8000/profile" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Logout:**
```bash
curl -X POST "http://localhost:8000/logout" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🔧 Development Setup

### Local Development (without Docker)

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MySQL database**
   ```bash
   # Start MySQL container only
   docker-compose up db -d
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Database Management

**View database schema:**
```bash
docker exec -it mysql_db mysql -u fastapi_user -p -e "USE auth_db; SHOW TABLES; DESCRIBE users;"
```

**View registered users:**
```bash
docker exec -it mysql_db mysql -u fastapi_user -p -e "USE auth_db; SELECT id, username, email, mobile_number FROM users;"
```

**Reset database:**
```bash
docker-compose down -v
docker-compose up --build
```

## 🚨 Security Considerations

1. **Secret Key**: Use a long, random secret key in production
2. **HTTPS**: Always use HTTPS in production
3. **Token Expiry**: Adjust token expiry based on security requirements
4. **Rate Limiting**: Implement rate limiting for auth endpoints
5. **Input Validation**: All inputs are validated and sanitized
6. **SQL Injection**: Protected by SQLAlchemy ORM
7. **Password Storage**: Passwords are bcrypt hashed

## 🐛 Troubleshooting

### Common Issues

**Port 8000 already in use:**
```bash
# Check what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Change port in docker-compose.yml
ports:
  - "8001:8000"
```

**Database connection error:**
```bash
# Restart with fresh database
docker-compose down -v
docker-compose up --build
```

**Token not working after logout:**
This is expected behavior - tokens are blacklisted on logout.

**"Method Not Allowed" on GET /register:**
Use POST method for registration and login endpoints.

## 📈 Performance Considerations

- **Token Blacklist Cleanup**: Implement periodic cleanup of expired blacklisted tokens
- **Session Cleanup**: Clean up inactive sessions periodically
- **Database Indexing**: Proper indexes on frequently queried fields
- **Connection Pooling**: SQLAlchemy handles connection pooling

## 🔮 Future Enhancements

- [ ] **Password Reset** functionality
- [ ] **Email Verification** for new accounts
- [ ] **OAuth Integration** (Google, Facebook)
- [ ] **Rate Limiting** for API endpoints
- [ ] **Admin Panel** for user management
- [ ] **Audit Logging** for security events
- [ ] **Multi-factor Authentication** (2FA)
- [ ] **API Versioning**
- [ ] **Comprehensive Unit Tests**
- [ ] **Performance Monitoring**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Your Name**
- GitHub: [@aarshsidana](https://github.com/aarshsidana)
- Email: aarshsidana@gmail.com

## 🙏 Acknowledgments

- FastAPI team for the amazing framework
- SQLAlchemy for the powerful ORM
- Pydantic for excellent validation
- Docker for containerization
- MySQL for reliable database
