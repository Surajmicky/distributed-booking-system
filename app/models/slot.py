from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text,text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Slot(Base):
    __tablename__ = "slots"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"), index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    capacity = Column(Integer, nullable=False)
    version = Column(Integer, default=0)
