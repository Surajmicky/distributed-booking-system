from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text,text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base

class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String, nullable=False)
    type = Column(String)
    meta_data = Column(JSONB)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())




