from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi import status as http_status
from app.models.booking import Booking
from app.models.slot import Slot
from app.models.seat import Seat
from app.models.resource import Resource
from app.schemas.booking import BookingResponse, BookingWithSlot, BookingListResponse, BookingStatus, BookingWithDetails, BookingListWithDetailsResponse, BookingMinimal, BookingListMinimalResponse
from app.schemas.resource import SlotResponse, ResourceResponse
from app.services.resource import ResourceService
from app.core.logging import logger

class BookingService:
    
    @staticmethod
    def create_booking(
        db: Session, 
        user_id: UUID, 
        seat_id: UUID
    ) -> BookingResponse:
        """Create a new booking"""
        logger.info(f"Creating booking for user {user_id}, seat {seat_id}")
        
        try:
            # Check if seat exists and is available
            seat = db.query(Seat).filter(Seat.id == seat_id).first()
            if not seat:
                logger.warning(f"Seat not found: {seat_id}")
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Seat not found"
                )
            
            # Check if seat is available
            if seat.status != "available":
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
            
            # Create the booking
            booking = Booking(
                user_id=user_id,
                seat_id=seat_id,
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
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create booking"
            )
    

    @staticmethod
    def get_user_bookings_with_details(
        db: Session, 
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[BookingStatus] = None
    ) -> BookingListMinimalResponse:
        """Get bookings for a user with minimal resource info"""
        logger.info(f"Fetching minimal bookings for user {user_id}, status={status}")
        
        try:
            query = db.query(Booking, Seat, Slot, Resource).join(Seat, Booking.seat_id == Seat.id).join(Slot, Seat.slot_id == Slot.id).join(Resource, Slot.resource_id == Resource.id).filter(
                Booking.user_id == user_id,
                Booking.status == BookingStatus.CONFIRMED
            )
            
            if status:
                query = query.filter(Booking.status == status)
            
            query = query.order_by(Booking.created_at.desc())
            
            total = query.count()
            booking_results = query.offset(skip).limit(limit).all()
            
            minimal_bookings = []
            for booking, seat, slot, resource in booking_results:
                minimal_booking = BookingMinimal(
                    id=booking.id,
                    user_id=booking.user_id,
                    seat_id=booking.seat_id,
                    status=booking.status,
                    created_at=booking.created_at,
                    resource_name=resource.name,
                    resource_type=resource.type,
                    slot_start_time=slot.start_time,
                    slot_end_time=slot.end_time,
                    seat_number=seat.seat_number,
                    seat_type=seat.seat_type
                )
                minimal_bookings.append(minimal_booking)
            
            logger.info(f"Found {len(minimal_bookings)} minimal bookings for user {user_id}")
            
            return BookingListMinimalResponse(
                bookings=minimal_bookings,
                total=total,
                page=skip // limit + 1 if limit > 0 else 1,
                size=limit
            )
            
        except Exception as e:
            logger.error(f"Error fetching minimal user bookings: {e}", exc_info=True)
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch bookings"
            )
    
    @staticmethod
    def get_booking_by_id(
        db: Session, 
        booking_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[BookingWithDetails]:
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
            
            # Get slot info from ResourceService
            slot_response = ResourceService.get_slot_with_availability(db, booking.slot_id)
            
            if not slot_response:
                logger.warning(f"Slot not found for booking {booking_id}")
                return None
            
            # Get resource details
            resource = db.query(Resource).filter(Resource.id == slot_response.resource_id).first()
            if not resource:
                logger.warning(f"Resource not found for booking {booking_id}")
                return None
                
            resource_response = ResourceResponse.model_validate(resource)
            
            booking_response = BookingWithDetails(
                id=booking.id,
                user_id=booking.user_id,
                slot_id=booking.slot_id,
                status=booking.status,
                created_at=booking.created_at,
                slot=slot_response,
                resource=resource_response
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
    
    @staticmethod
    def get_all_user_bookings(
        db: Session, 
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[BookingStatus] = None
    ) -> BookingListResponse:
        """Get all bookings for a user including cancelled (admin endpoint)"""
        logger.info(f"Fetching all bookings for user {user_id}, status={status}")
        
        try:
            query = db.query(Booking).filter(Booking.user_id == user_id)
            
            if status:
                query = query.filter(Booking.status == status)
            
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
            logger.error(f"Error fetching all user bookings: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch bookings"
            )