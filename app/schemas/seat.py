from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class SeatStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"

class SeatBase(BaseModel):
    seat_number: str
    seat_type: str = "standard"
    meta_data: Optional[str] = None

class SeatCreate(SeatBase):
    slot_id: UUID

class SeatResponse(SeatBase):
    id: UUID
    slot_id: UUID
    status: SeatStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SeatWithSlot(SeatResponse):
    slot: "SlotResponse" = None

class SeatListResponse(BaseModel):
    seats: List[SeatResponse]
    total: int
    page: int
    size: int

# Forward reference to avoid circular import
from app.schemas.resource import SlotResponse
SeatWithSlot.model_rebuild()
