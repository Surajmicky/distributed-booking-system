from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi import status as http_status
from app.models.seat import Seat, SeatStatus
from app.models.slot import Slot
from app.models.resource import Resource
from app.models.booking import Booking
from app.schemas.seat import SeatResponse, SeatListResponse
from app.schemas.booking import BookingStatus
from app.core.logging import logger

class SeatService:
    
    @staticmethod
    def get_available_seats_for_slot(
        db: Session, 
        slot_id: UUID,
        seat_type: Optional[str] = None
    ) -> List[SeatResponse]:
        """Get available seats for a specific slot"""
        logger.info(f"Fetching available seats for slot {slot_id}, type={seat_type}")
        
        try:
            query = db.query(Seat).filter(
                Seat.slot_id == slot_id,
                Seat.status == SeatStatus.AVAILABLE
            )
            
            if seat_type:
                query = query.filter(Seat.seat_type == seat_type)
            
            seats = query.order_by(Seat.seat_number).all()
            
            logger.info(f"Found {len(seats)} available seats for slot {slot_id}")
            
            return [SeatResponse.model_validate(seat) for seat in seats]
            
        except Exception as e:
            logger.error(f"Error fetching available seats: {e}", exc_info=True)
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch available seats"
            )
    
    @staticmethod
    def book_seat_with_lock(
        db: Session, 
        seat_id: UUID,
        user_id: UUID
    ) -> Booking:
        """Book a specific seat with row-level locking"""
        logger.info(f"Booking seat {seat_id} for user {user_id}")
        
        try:
            # Lock the seat row for atomic operation
            seat = db.query(Seat).filter(Seat.id == seat_id).with_for_update().first()
            
            if not seat:
                logger.warning(f"Seat not found: {seat_id}")
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Seat not found"
                )
            
            if seat.status != SeatStatus.AVAILABLE:
                logger.warning(f"Seat {seat_id} not available, status: {seat.status}")
                raise HTTPException(
                    status_code=http_status.HTTP_409_CONFLICT,
                    detail="Seat is not available"
                )
            
            # Check if slot is in the future
            slot = db.query(Slot).filter(Slot.id == seat.slot_id).first()
            if slot and slot.start_time <= datetime.now(timezone.utc):
                logger.warning(f"Attempted to book past slot: {slot.id}")
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Cannot book seats for past time slots"
                )
            
            # Check if user already has a booking for this slot
            existing_booking = db.query(Booking).join(Seat).filter(
                Booking.user_id == user_id,
                Seat.slot_id == seat.slot_id,
                Booking.status == BookingStatus.CONFIRMED
            ).first()
            
            if existing_booking:
                logger.warning(f"User {user_id} already has booking for slot {seat.slot_id}")
                raise HTTPException(
                    status_code=http_status.HTTP_409_CONFLICT,
                    detail="You already have a booking for this time slot"
                )
            
            # Update seat status
            seat.status = SeatStatus.BOOKED
            
            # Create booking
            booking = Booking(
                user_id=user_id,
                seat_id=seat_id,
                status=BookingStatus.CONFIRMED
            )
            
            db.add(booking)
            db.commit()
            db.refresh(booking)
            
            logger.info(f"Seat {seat_id} booked successfully for user {user_id}")
            return booking
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error booking seat: {e}", exc_info=True)
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to book seat"
            )
    
    @staticmethod
    def release_seat(
        db: Session, 
        seat_id: UUID
    ) -> Seat:
        """Release a seat back to available status"""
        logger.info(f"Releasing seat {seat_id}")
        
        try:
            seat = db.query(Seat).filter(Seat.id == seat_id).with_for_update().first()
            
            if not seat:
                logger.warning(f"Seat not found for release: {seat_id}")
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Seat not found"
                )
            
            if seat.status != SeatStatus.BOOKED:
                logger.warning(f"Seat {seat_id} is not booked, status: {seat.status}")
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Seat is not currently booked"
                )
            
            seat.status = SeatStatus.AVAILABLE
            db.commit()
            db.refresh(seat)
            
            logger.info(f"Seat {seat_id} released successfully")
            return seat
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error releasing seat: {e}", exc_info=True)
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to release seat"
            )
