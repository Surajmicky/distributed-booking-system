from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session as DBSession
from jose import JWTError, jwt
from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.models.user import User
from app.models.session import Session as SessionModel
import secrets
from datetime import datetime, timedelta
from passlib.context import CryptContext
import hashlib


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
    except JWTError as e:
        logger.error(f"JWT token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: DBSession = Depends(get_db)) -> User:
    """
    Get current authenticated user from JWT token
    """
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT token missing subject")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found for ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create JWT access token
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        
        logger.debug(f"Access token created for user: {data.get('sub')}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Error creating access token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation failed"
        )


def create_refresh_token(user_id: str) -> str:
    """
    Create JWT refresh token
    """
    try:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        
        logger.debug(f"Refresh token created for user: {user_id}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Error creating refresh token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Refresh token creation failed"
        )



def hash_refresh_token(refresh_token: str) -> str:
    """
    Hash refresh token for database storage using SHA-256 (deterministic)
    """
    try:
        # Use SHA-256 for deterministic hashing
        return hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
        
    except Exception as e:
        logger.error(f"Error hashing refresh token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token hashing failed"
        )


def validate_refresh_token(refresh_token: str, db: DBSession) -> str:
    """
    Validate JWT refresh token and check against database
    """
    logger.debug("Validating refresh token")
    
    try:
        payload = jwt.decode(
            refresh_token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type provided for refresh")
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Refresh token missing subject")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if this specific refresh token exists in database and not expired
        token_hash = hash_refresh_token(refresh_token)
        session = (
            db.query(SessionModel)
            .filter(
                SessionModel.refresh_token_hash == token_hash,
                SessionModel.user_id == user_id,
                SessionModel.expires_at > datetime.utcnow()
            )
            .first()
        )
        
        if not session:
            logger.warning(f"Invalid or expired refresh token for user: {user_id}")
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
        logger.debug(f"Refresh token validated successfully for user: {user_id}")
        return user_id
        
    except JWTError as je:
        logger.error(f"JWT error during refresh token validation: {je}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during refresh token validation: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Token validation failed")


def revoke_refresh_token(refresh_token: str, db: DBSession) -> None:
    """
    Revoke refresh token by removing from database
    """
    logger.debug("Revoking refresh token")
    
    try:
        # Decode token to get user_id
        payload = jwt.decode(
            refresh_token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Cannot revoke token: missing subject")
            return
        
        # Hash the token and find the session
        token_hash = hash_refresh_token(refresh_token)
        session = (
            db.query(SessionModel)
            .filter(
                SessionModel.refresh_token_hash == token_hash,
                SessionModel.user_id == user_id
            )
            .first()
        )
        
        if session:
            db.delete(session)
            logger.debug(f"Refresh token revoked for user: {user_id}")
        else:
            logger.warning(f"Session not found for token revocation, user: {user_id}")
            
    except JWTError as je:
        logger.error(f"JWT error during token revocation: {je}")
    except Exception as e:
        logger.error(f"Error during token revocation: {e}", exc_info=True)

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with proper handling of length limits
    """
    try:
        # Encode password to bytes and truncate to 72 bytes (bcrypt limit)
        password_bytes = password.encode('utf-8')[:72]
        # Decode back to string for passlib
        truncated_password = password_bytes.decode('utf-8', errors='ignore')
        
        hashed = pwd_context.hash(truncated_password)
        logger.debug("Password hashed successfully")
        return hashed
        
    except Exception as e:
        logger.error(f"Error hashing password: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password hashing failed"
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    """
    try:
        # Encode password to bytes and truncate to 72 bytes (bcrypt limit)
        password_bytes = plain_password.encode('utf-8')[:72]
        # Decode back to string for passlib
        truncated_password = password_bytes.decode('utf-8', errors='ignore')
        
        is_valid = pwd_context.verify(truncated_password, hashed_password)
        
        if is_valid:
            logger.debug("Password verification successful")
        else:
            logger.warning("Password verification failed")
            
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying password: {e}", exc_info=True)
        return False