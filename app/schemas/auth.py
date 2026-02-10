from pydantic import BaseModel, EmailStr
from app.schemas.user import UserResponse

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str  # subject (user_id)
    exp: int  # expiration time

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse

# Alias for compatibility
LoginRequest = UserLogin
