from sqlalchemy import Column, String, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    seat_id = Column(UUID(as_uuid=True), ForeignKey("seats.id"), index=True)
    status = Column(String, default="confirmed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
