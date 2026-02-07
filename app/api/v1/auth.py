from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from app.db.session import get_db
from app.schemas.user import UserRegister
from app.schemas.auth import UserLogin, TokenRefresh, AuthResponse, TokenResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: DBSession = Depends(get_db)):
    """
    Register a new user
    """
    return AuthService.register_user(user_data.email, user_data.password, db)

@router.post("/login", response_model=AuthResponse)
async def login(user_data: UserLogin, db: DBSession = Depends(get_db)):
    """
    Login user and return tokens
    """
    return AuthService.login_user(user_data.email, user_data.password, db)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefresh, db: DBSession = Depends(get_db)):
    """
    Refresh access token
    """
    return AuthService.refresh_tokens(request.refresh_token, db)

@router.post("/logout")
async def logout(request: TokenRefresh, db: DBSession = Depends(get_db)):
    """
    Logout user (revoke refresh token)
    """
    AuthService.logout_user(request.refresh_token, db)
    return {"message": "Successfully logged out"}