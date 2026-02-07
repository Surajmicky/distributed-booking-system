from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session as DBSession
from jose import JWTError, jwt
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
import secrets
from datetime import datetime, timedelta
from passlib.context import CryptContext
from app.models.session import Session as SessionModel

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode a JWT token
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DBSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token
    """
    try:
        payload = verify_jwt_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    return jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )



def create_refresh_token() -> str:
    """
    Create a cryptographically secure refresh token
    """
    return secrets.token_urlsafe(32)
 
def hash_refresh_token(token: str) -> str:
    """
    Hash refresh token for storage in database
    """
    return pwd_context.hash(token)
 
def verify_refresh_token(plain_token: str, hashed_token: str) -> bool:
    """
    Verify refresh token against stored hash
    """
    return pwd_context.verify(plain_token, hashed_token)

def create_token_pair(user_id: str, db: DBSession) -> dict:
    """
    Create both access and refresh tokens for a user
    Stores refresh token hash in database
    Allows multiple concurrent sessions per user
    """
    # Create access token
    access_token_data = {"sub": user_id}
    access_token = create_access_token(access_token_data)
    
    # Create refresh token
    refresh_token = create_refresh_token()
    refresh_token_hash = hash_refresh_token(refresh_token)
    
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Create new session 
    session = SessionModel(
        user_id=user_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
 
def revoke_refresh_token(refresh_token: str, db: DBSession) -> None:
    """
    Revoke a specific refresh token 
    """
    token_hash = hash_refresh_token(refresh_token)

    session = (
        db.query(SessionModel)
        .filter(SessionModel.refresh_token_hash == token_hash)
        .first()
    )

    if session:
        db.delete(session)
        db.commit()


def validate_refresh_token(refresh_token: str, db: DBSession) -> str:
    """
    Validate refresh token and return user_id
    """
    token_hash = hash_refresh_token(refresh_token)

    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.refresh_token_hash == token_hash,
            SessionModel.expires_at > datetime.utcnow()
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return str(session.user_id)

    # Add these functions to app/middleware/auth.py

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    """
    return pwd_context.verify(plain_password, hashed_password)