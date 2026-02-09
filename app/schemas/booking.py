# app/schemas/booking.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.resource import SlotResponse
from uuid import UUID
from enum import Enum

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class BookingBase(BaseModel):
    slot_id: UUID

class BookingCreate(BookingBase):
    pass

class BookingResponse(BaseModel):
    id: UUID
    user_id: UUID
    slot_id: UUID
    status: BookingStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

class BookingWithSlot(BookingResponse):
    slot: "SlotResponse" = None
BookingWithSlot.model_rebuild()

class BookingListResponse(BaseModel):
    bookings: List[BookingResponse]
    total: int
    page: int
    size: int

class BookingCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500, description="Optional cancellation reason")

class BookingUpdateRequest(BaseModel):
    status: Optional[BookingStatus] = None