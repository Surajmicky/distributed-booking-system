from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from app.db.base import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()