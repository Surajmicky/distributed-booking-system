from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException, status
from app.models.user import User
from app.models.session import Session as SessionModel
from app.schemas.auth import AuthResponse, TokenResponse
from app.schemas.user import UserResponse
from datetime import datetime, timedelta
from app.core.logging import logger
from app.core.config import settings

from app.middleware.auth import (
    validate_refresh_token,
    create_refresh_token, 
    hash_refresh_token,
    create_access_token,
    hash_password,
    verify_password,
    revoke_refresh_token
)

class AuthService:
    
    @staticmethod
    def register_user(email: str, password: str, db: DBSession) -> AuthResponse:
        """
        Register a new user and return tokens
        """
        logger.info(f"Registration attempt for email: {email}")
        
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                logger.warning(f"Registration failed: Email already exists - {email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create new user
            password_hash = hash_password(password)
            user = User(email=email, password_hash=password_hash)
            db.add(user)
            db.flush()  # Get the ID without committing
            
            logger.info(f"User created successfully: {user.id}")
            
            # Create tokens
            access_token = create_access_token({"sub": str(user.id)})
            refresh_token = create_refresh_token(str(user.id))
            
            # Store refresh token hash in database
            refresh_token_hash = hash_refresh_token(refresh_token)
            expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            session = SessionModel(
                user_id=user.id,
                refresh_token_hash=refresh_token_hash,
                expires_at=expires_at
            )
            db.add(session)
            
            # Commit everything at once
            db.commit()
            db.refresh(user)
            
            logger.info(f"Registration successful for user: {user.id}")
            
            # Build response
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                created_at=user.created_at.isoformat()
            )
            
            token_response = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
            
            return AuthResponse(user=user_response, tokens=token_response)
            
        except HTTPException as he:
            logger.error(f"HTTP Exception during registration: {he.detail}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Database Exception during registration: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )

    @staticmethod
    def login_user(email: str, password: str, db: DBSession) -> AuthResponse:
        """
        Authenticate user and return tokens
        """
        logger.info(f"Login attempt for email: {email}")
        
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            if not user:
                logger.warning(f"Login failed: User not found - {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Verify password
            if not verify_password(password, user.password_hash):
                logger.warning(f"Login failed: Invalid password - {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Create tokens
            access_token = create_access_token({"sub": str(user.id)})
            refresh_token = create_refresh_token(str(user.id))
            
            # Store refresh token hash in database
            refresh_token_hash = hash_refresh_token(refresh_token)
            expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            session = SessionModel(
                user_id=user.id,
                refresh_token_hash=refresh_token_hash,
                expires_at=expires_at
            )
            db.add(session)
            
            # Commit everything at once
            db.commit()
            
            logger.info(f"Login successful for user: {user.id}")
            
            # Build response
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                created_at=user.created_at.isoformat()
            )
            
            token_response = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
            
            return AuthResponse(user=user_response, tokens=token_response)
            
        except HTTPException as he:
            logger.error(f"HTTP Exception during login: {he.detail}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Database Exception during login: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )

    @staticmethod
    def refresh_tokens(refresh_token: str, db: DBSession) -> TokenResponse:
        """
        Refresh access token using refresh token
        """
        logger.info("Token refresh attempt")
        
        try:
            user_id = validate_refresh_token(refresh_token, db)
            
            # Create new access token
            access_token = create_access_token({"sub": user_id})
            
            logger.info(f"Token refresh successful for user: {user_id}")
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,  # Return same refresh token
                token_type="bearer"
            )
            
        except HTTPException as he:
            logger.error(f"HTTP Exception during token refresh: {he.detail}")
            raise
        except Exception as e:
            logger.error(f"Exception during token refresh: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed"
            )

    @staticmethod
    def logout_user(refresh_token: str, db: DBSession) -> None:
        """
        Logout user (revoke refresh token)
        """
        logger.info("Logout attempt")
        
        try:
            revoke_refresh_token(refresh_token, db)
            db.commit()
            logger.info("Logout successful")
        except Exception as e:
            db.rollback()
            logger.error(f"Exception during logout: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )