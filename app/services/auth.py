from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import AuthResponse, TokenResponse
from app.schemas.user import UserResponse
from app.middleware.auth import (
    create_token_pair, 
    validate_refresh_token, 
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
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        password_hash = hash_password(password)
        user = User(email=email, password_hash=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create tokens
        tokens = create_token_pair(str(user.id), db)
        
        # Build response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at.isoformat()
        )
        
        token_response = TokenResponse(**tokens)
        
        return AuthResponse(user=user_response, tokens=token_response)
    
    @staticmethod
    def login_user(email: str, password: str, db: DBSession) -> AuthResponse:
        """
        Authenticate user and return tokens
        """
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create tokens
        tokens = create_token_pair(str(user.id), db)
        
        # Build response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at.isoformat()
        )
        
        token_response = TokenResponse(**tokens)
        
        return AuthResponse(user=user_response, tokens=token_response)
    
    @staticmethod
    def refresh_tokens(refresh_token: str, db: DBSession) -> TokenResponse:
        """
        Refresh access token using refresh token
        """
        user_id = validate_refresh_token(refresh_token, db)
        
        # Create new access token
        access_token = create_access_token({"sub": user_id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Return same refresh token
            token_type="bearer"
        )
    
    @staticmethod
    def logout_user(refresh_token: str, db: DBSession) -> None:
        """
        Logout user (revoke refresh token)
        """
        revoke_refresh_token(refresh_token, db)