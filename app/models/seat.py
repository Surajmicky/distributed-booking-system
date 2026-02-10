from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.db.base import Base

class SeatStatus(str, PyEnum):
    AVAILABLE = "available"
    BOOKED = "booked"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"

class Seat(Base):
    __tablename__ = "seats"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    slot_id = Column(UUID(as_uuid=True), ForeignKey("slots.id"), index=True, nullable=False)
    seat_number = Column(String, nullable=False)  # e.g., "A1", "B2", "Window-1"
    status = Column(String, default=SeatStatus.AVAILABLE, nullable=False)
    seat_type = Column(String, default="standard") 
    meta_data = Column(Text)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
