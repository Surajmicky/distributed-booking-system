# app/schemas/booking.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.resource import SlotResponse, ResourceResponse
from uuid import UUID
from enum import Enum

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class BookingBase(BaseModel):
    seat_id: UUID

class BookingCreate(BookingBase):
    pass

class BookingResponse(BaseModel):
    id: UUID
    user_id: UUID
    seat_id: UUID
    status: BookingStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

class BookingWithSlot(BookingResponse):
    slot: "SlotResponse" = None

class BookingWithDetails(BookingResponse):
    slot: "SlotResponse" = None
    resource: "ResourceResponse" = None
    seat: "SeatResponse" = None

class BookingMinimal(BaseModel):
    id: UUID
    user_id: UUID
    seat_id: UUID
    status: BookingStatus
    created_at: datetime
    resource_name: str
    resource_type: str
    slot_start_time: datetime
    slot_end_time: datetime
    seat_number: str
    seat_type: str
    
    class Config:
        from_attributes = True

class BookingListResponse(BaseModel):
    bookings: List[BookingResponse]
    total: int
    page: int
    size: int

class BookingListMinimalResponse(BaseModel):
    bookings: List[BookingMinimal]
    total: int
    page: int
    size: int

class BookingListWithDetailsResponse(BaseModel):
    bookings: List[BookingWithDetails]
    total: int
    page: int
    size: int

class BookingCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500, description="Optional cancellation reason")

class BookingUpdateRequest(BaseModel):
    status: Optional[BookingStatus] = None

# Forward reference resolution
from app.schemas.seat import SeatResponse
BookingWithSlot.model_rebuild()
BookingWithDetails.model_rebuild()