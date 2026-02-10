from .user import UserResponse, UserRegister
from .auth import Token, TokenData, LoginRequest
from .resource import (
    ResourceResponse, 
    ResourceWithSlots, 
    SlotResponse,
    ResourceListResponse,
    ResourceCreate
)
from .seat import (
    SeatResponse,
    SeatCreate,
    SeatWithSlot,
    SeatListResponse,
    SeatStatus
)
from .booking import (
    BookingCreate,
    BookingResponse,
    BookingWithSlot,
    BookingListResponse,
    BookingStatus,
    BookingCancelRequest,
    BookingUpdateRequest,
    BookingWithDetails,
    BookingListWithDetailsResponse,
    BookingMinimal,
    BookingListMinimalResponse
)

__all__ = [
    "UserResponse", 
    "UserRegister",
    "Token", 
    "TokenData", 
    "LoginRequest",
    "ResourceResponse",
    "ResourceWithSlots", 
    "SlotResponse",
    "ResourceListResponse",
    "ResourceCreate",
    "SeatResponse",
    "SeatCreate",
    "SeatWithSlot",
    "SeatListResponse",
    "SeatStatus",
    "BookingCreate",
    "BookingResponse",
    "BookingWithSlot",
    "BookingListResponse",
    "BookingStatus",
    "BookingCancelRequest",
    "BookingUpdateRequest",
    "BookingWithDetails",
    "BookingListWithDetailsResponse",
    "BookingMinimal",
    "BookingListMinimalResponse"
]