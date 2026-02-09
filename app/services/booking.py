from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.models.booking import Booking
from app.models.slot import Slot
from app.models.resource import Resource
from app.schemas.booking import BookingResponse, BookingWithSlot, BookingListResponse, BookingStatus
from app.schemas.resource import SlotResponse
from app.core.logging import logger

class BookingService:
    
    @staticmethod
    def create_booking(
        db: Session, 
        user_id: UUID, 
        slot_id: UUID
    ) -> BookingResponse:
        """Create a new booking"""
        logger.info(f"Creating booking for user {user_id}, slot {slot_id}")
        
        try:
            # Check if slot exists and is available
            slot = db.query(Slot).filter(Slot.id == slot_id).first()
            if not slot:
                logger.warning(f"Slot not found: {slot_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Slot not found"
                )
            
            # Check if slot is in the future
            if slot.start_time <= datetime.now(timezone.utc):
                logger.warning(f"Attempted to book past slot: {slot_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot book past time slots"
                )
            
            # Check if slot is already booked
            existing_booking = db.query(Booking).filter(
                Booking.slot_id == slot_id,
                Booking.status == BookingStatus.CONFIRMED
            ).first()
            
            if existing_booking:
                logger.warning(f"Slot already booked: {slot_id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Slot is already booked"
                )
            
            # Check if user already has a booking for this slot
            user_existing_booking = db.query(Booking).filter(
                Booking.user_id == user_id,
                Booking.slot_id == slot_id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
            ).first()
            
            if user_existing_booking:
                logger.warning(f"User {user_id} already booked slot {slot_id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You already have a booking for this slot"
                )
            
            # Create the booking
            booking = Booking(
                user_id=user_id,
                slot_id=slot_id,
                status=BookingStatus.CONFIRMED
            )
            
            db.add(booking)
            db.commit()
            db.refresh(booking)
            
            logger.info(f"Booking created successfully: {booking.id}")
            return BookingResponse.model_validate(booking)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating booking: {e}", exc_info=True)
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create booking"
            )
    
    @staticmethod
    def get_user_bookings(
        db: Session, 
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[BookingStatus] = None
    ) -> BookingListResponse:
        """Get bookings for a specific user"""
        logger.info(f"Fetching bookings for user {user_id}, status={status}")
        
        try:
            query = db.query(Booking).filter(Booking.user_id == user_id)
            
            if status:
                query = query.filter(Booking.status == status)
            
            # Order by creation time (newest first)
            query = query.order_by(Booking.created_at.desc())
            
            total = query.count()
            bookings = query.offset(skip).limit(limit).all()
            
            logger.info(f"Found {total} bookings for user {user_id}")
            
            return BookingListResponse(
                bookings=[BookingResponse.model_validate(booking) for booking in bookings],
                total=total,
                page=skip // limit + 1 if limit > 0 else 1,
                size=limit
            )
            
        except Exception as e:
            logger.error(f"Error fetching user bookings: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch bookings"
            )
    
    @staticmethod
    def get_booking_by_id(
        db: Session, 
        booking_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[BookingWithSlot]:
        """Get a specific booking by ID (with slot details)"""
        logger.info(f"Fetching booking {booking_id} for user {user_id}")
        
        try:
            # Get booking first
            query = db.query(Booking).filter(Booking.id == booking_id)
            
            # If user_id is provided, ensure booking belongs to user
            if user_id:
                query = query.filter(Booking.user_id == user_id)
            
            booking = query.first()
            
            if not booking:
                logger.warning(f"Booking not found: {booking_id}")
                return None
            
            # Get slot separately
            slot = db.query(Slot).filter(Slot.id == booking.slot_id).first()
            if not slot:
                logger.warning(f"Slot not found for booking {booking_id}")
                return None
            
            # Create slot response
            slot_response = SlotResponse(
                id=slot.id,
                resource_id=slot.resource_id,
                start_time=slot.start_time,
                end_time=slot.end_time,
                capacity=slot.capacity,
                version=slot.version
            )
            
            booking_response = BookingWithSlot(
                id=booking.id,
                user_id=booking.user_id,
                slot_id=booking.slot_id,
                status=booking.status,
                created_at=booking.created_at,
                slot=slot_response
            )
            
            logger.info(f"Booking found: {booking_id}")
            return booking_response
            
        except Exception as e:
            logger.error(f"Error fetching booking {booking_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch booking"
            )
    @staticmethod
    def cancel_booking(
        db: Session, 
        booking_id: UUID,
        user_id: UUID
    ) -> BookingResponse:
        """Cancel a booking"""
        logger.info(f"Cancelling booking {booking_id} for user {user_id}")
        
        try:
            booking = db.query(Booking).filter(
                Booking.id == booking_id,
                Booking.user_id == user_id
            ).first()
            
            if not booking:
                logger.warning(f"Booking not found for cancellation: {booking_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found"
                )
            
            if booking.status == BookingStatus.CANCELLED:
                logger.warning(f"Booking already cancelled: {booking_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Booking is already cancelled"
                )
            
            # Check if slot is in the past (can't cancel past bookings)
            slot = db.query(Slot).filter(Slot.id == booking.slot_id).first()
            if slot.start_time <= datetime.now(timezone.utc):
                logger.warning(f"Attempted to cancel past booking: {booking_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel bookings for past time slots"
                )
            
            # Update booking status
            booking.status = BookingStatus.CANCELLED
            db.commit()
            db.refresh(booking)
            
            logger.info(f"Booking cancelled successfully: {booking_id}")
            return BookingResponse.model_validate(booking)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}", exc_info=True)
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel booking"
            )
    
    @staticmethod
    def get_slot_bookings(
        db: Session, 
        slot_id: UUID
    ) -> List[BookingResponse]:
        """Get all bookings for a specific slot"""
        logger.info(f"Fetching bookings for slot {slot_id}")
        
        try:
            bookings = db.query(Booking).filter(
                Booking.slot_id == slot_id,
                Booking.status == BookingStatus.CONFIRMED
            ).order_by(Booking.created_at.asc()).all()
            
            logger.info(f"Found {len(bookings)} bookings for slot {slot_id}")
            
            return [BookingResponse.model_validate(booking) for booking in bookings]
            
        except Exception as e:
            logger.error(f"Error fetching slot bookings: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch slot bookings"
            )