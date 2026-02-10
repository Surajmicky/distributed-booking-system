from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.services.booking import BookingService
from app.schemas.booking import (
    BookingCreate, 
    BookingResponse, 
    BookingWithSlot, 
    BookingListResponse,
    BookingStatus,
    BookingCancelRequest,
    BookingListWithDetailsResponse,
    BookingListMinimalResponse,
    BookingWithDetails
)
from app.middleware.auth import get_current_user
from app.schemas.user import UserResponse
from app.core.logging import logger

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new booking for a specific seat"""
    logger.info(f"API request: POST /bookings/ - user={current_user.id}, seat={booking_data.seat_id}")
    
    try:
        return BookingService.create_booking(
            db=db,
            user_id=current_user.id,
            seat_id=booking_data.seat_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_booking: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/", response_model=BookingListMinimalResponse)
def get_user_bookings_with_details(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current user's bookings with minimal resource info"""
    logger.info(f"API request: GET /bookings/ - user={current_user.id}, status={status}")
    
    try:
        return BookingService.get_user_bookings_with_details(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_bookings_with_details: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/{booking_id}", response_model=BookingWithDetails)
def get_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific booking by ID"""
    logger.info(f"API request: GET /bookings/{booking_id} - user={current_user.id}")
    
    try:
        booking = BookingService.get_booking_by_id(
            db=db,
            booking_id=booking_id,
            user_id=current_user.id
        )
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        return booking
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_booking: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: UUID,
    cancel_data: Optional[BookingCancelRequest] = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Cancel a booking"""
    logger.info(f"API request: POST /bookings/{booking_id}/cancel - user={current_user.id}")
    
    try:
        return BookingService.cancel_booking(
            db=db,
            booking_id=booking_id,
            user_id=current_user.id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in cancel_booking: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

# Admin endpoints (for future use)
@router.get("/slot/{slot_id}", response_model=List[BookingResponse])
def get_slot_bookings(
    slot_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all bookings for a specific slot (admin endpoint)"""
    logger.info(f"API request: GET /bookings/slot/{slot_id} - user={current_user.id}")
    
    try:
        # TODO: Add admin role check
        return BookingService.get_slot_bookings(db=db, slot_id=slot_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_slot_bookings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/admin/{user_id}", response_model=BookingListResponse)
def get_all_user_bookings_admin(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[BookingStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all bookings for a user including cancelled (admin endpoint)"""
    logger.info(f"API request: GET /bookings/admin/{user_id} - admin={current_user.id}")
    
    try:
        # TODO: Add admin role check
        return BookingService.get_all_user_bookings(
            db=db,
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_all_user_bookings_admin: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )