# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from app.db.session import get_db
from app.schemas.user import UserRegister
from app.schemas.auth import UserLogin, TokenRefresh, AuthResponse, TokenResponse
from app.services.auth import AuthService
from app.core.logging import logger

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: DBSession = Depends(get_db)):
    """
    Register a new user
    """
    logger.info(f"API request: POST /auth/register - email={user_data.email}")
    
    try:
        return AuthService.register_user(user_data.email, user_data.password, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in register: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Registration failed due to internal server error"
        )

@router.post("/login", response_model=AuthResponse)
async def login(user_data: UserLogin, db: DBSession = Depends(get_db)):
    """
    Login user and return tokens
    """
    logger.info(f"API request: POST /auth/login - email={user_data.email}")
    
    try:
        return AuthService.login_user(user_data.email, user_data.password, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Login failed due to internal server error"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefresh, db: DBSession = Depends(get_db)):
    """
    Refresh access token
    """
    logger.info("API request: POST /auth/refresh")
    
    try:
        return AuthService.refresh_tokens(request.refresh_token, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in refresh_token: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Token refresh failed due to internal server error"
        )

@router.post("/logout")
async def logout(request: TokenRefresh, db: DBSession = Depends(get_db)):
    """
    Logout user (revoke refresh token)
    """
    logger.info("API request: POST /auth/logout")
    
    try:
        AuthService.logout_user(request.refresh_token, db)
        return {"message": "Successfully logged out"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in logout: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Logout failed due to internal server error"
        )