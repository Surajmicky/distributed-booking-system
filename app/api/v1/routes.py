import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User

router = APIRouter()

@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"users": users}

@router.get("/users/{user_uuid}")
async def get_user(user_uuid: uuid.UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_uuid == user_uuid).first()
    if not user:
        return {"error": "User not found"}
    return {"user": user}

@router.post("/users")
async def create_user(user_data: dict, db: Session = Depends(get_db)):
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user": user}

@router.put("/users/{user_uuid}")
async def update_user(user_uuid: uuid.UUID, user_data: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_uuid == user_uuid).first()
    if not user:
        return {"error": "User not found"}
    
    for key, value in user_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return {"user": user}