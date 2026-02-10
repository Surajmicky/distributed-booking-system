# app/services/resource_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.models.resource import Resource
from app.models.slot import Slot
from app.models.seat import Seat
from app.models.booking import Booking
from app.schemas.resource import ResourceResponse, ResourceWithSlots, SlotResponse, ResourceListResponse
from app.schemas.seat import SeatResponse as SeatResponseSchema
from app.core.logging import logger


class ResourceService:
    
    @staticmethod
    def get_all_resources(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        resource_type: Optional[str] = None
    ) -> ResourceListResponse:
        """Get all resources with pagination and optional type filter"""
        logger.info(f"Fetching resources: skip={skip}, limit={limit}, type={resource_type}")
        
        try:
            query = db.query(Resource)
            
            if resource_type:
                query = query.filter(Resource.type == resource_type)
                logger.info(f"Filtering resources by type: {resource_type}")
            
            total = query.count()
            resources = query.offset(skip).limit(limit).all()
            
            logger.info(f"Found {total} total resources, returning {len(resources)}")
            
            return ResourceListResponse(
                resources=[ResourceResponse.model_validate(resource) for resource in resources],
                total=total,
                page=skip // limit + 1 if limit > 0 else 1,
                size=limit
            )
            
        except Exception as e:
            logger.error(f"Error fetching resources: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch resources"
            )
    
    @staticmethod
    def get_resource_by_id(db: Session, resource_id: UUID) -> Optional[ResourceResponse]:
        """Get resource by ID"""
        logger.info(f"Fetching resource by ID: {resource_id}")
        
        try:
            resource = db.query(Resource).filter(Resource.id == resource_id).first()
            
            if not resource:
                logger.warning(f"Resource not found: {resource_id}")
                return None
            
            logger.info(f"Resource found: {resource_id}")
            return ResourceResponse.model_validate(resource)
            
        except Exception as e:
            logger.error(f"Error fetching resource {resource_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch resource"
            )
    
    @staticmethod
    def get_resource_with_slots(
        db: Session, 
        resource_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[ResourceWithSlots]:
        """Get resource with its available slots (future slots only, not booked)"""
        logger.info(f"Fetching resource with slots: {resource_id}, start_date={start_date}, end_date={end_date}")
    
        try:
            resource = db.query(Resource).filter(Resource.id == resource_id).first()
            
            if not resource:
                logger.warning(f"Resource not found for slots query: {resource_id}")
                return None
            
            # Default to current time if no start_date provided
            current_time = datetime.utcnow()
            effective_start_date = start_date if start_date else current_time
            
            query = db.query(Slot).filter(
                Slot.resource_id == resource_id,
                Slot.start_time >= effective_start_date  # Only future slots
            )
            
            if end_date:
                query = query.filter(Slot.end_time <= end_date)
                logger.info(f"Filtering slots until end_date: {end_date}")
            
            # Get slots with all seats in single query
            slots_with_seats = db.query(
                Slot,
                Seat
            ).outerjoin(
                Seat,
                Slot.id == Seat.slot_id
            ).filter(
                Slot.resource_id == resource_id,
                Slot.start_time >= effective_start_date
            ).order_by(Slot.start_time, Seat.seat_number).all()
            
            if end_date:
                slots_with_seats = [s for s in slots_with_seats if s[0].end_time <= end_date]
            
            # Group seats by slot
            slots_dict = {}
            for slot, seat in slots_with_seats:
                if slot.id not in slots_dict:
                    slots_dict[slot.id] = {
                        'slot': slot,
                        'seats': []
                    }
                if seat:
                    slots_dict[slot.id]['seats'].append(seat)
            
            # Build slot responses with seat details
            slot_responses = []
            for slot_data in slots_dict.values():
                slot = slot_data['slot']
                seats = slot_data['seats']
                
                # Only include slots that have available seats
                available_seats = [s for s in seats if s.status == 'available']
                if available_seats:
                    # Convert seats to SeatResponse objects
                    seat_responses = [SeatResponseSchema.model_validate(seat) for seat in seats]
                    
                    slot_response = SlotResponse(
                        id=slot.id,
                        resource_id=slot.resource_id,
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        version=slot.version,
                        seats=seat_responses
                    )
                    slot_responses.append(slot_response)
            
            logger.info(f"Found {len(slot_responses)} available slots for resource {resource_id}")
            
            return ResourceWithSlots(
                id=resource.id,
                name=resource.name,
                type=resource.type,
                meta_data=resource.meta_data,
                created_at=resource.created_at,
                slots=slot_responses
            )
            
        except Exception as e:
            logger.error(f"Error fetching resource with slots {resource_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch resource with slots"
            )   
            
    @staticmethod
    def get_slot_with_availability(db: Session, slot_id: UUID) -> Optional[SlotResponse]:
        """Get slot with remaining capacity"""
        try:
            slot_with_count = db.query(
                Slot,
                func.count(Seat.id).label('available_count')
            ).outerjoin(
                Seat,
                and_(Slot.id == Seat.slot_id, Seat.status == 'available')
            ).filter(Slot.id == slot_id).group_by(Slot.id).first()
            
            if not slot_with_count:
                return None
            
            slot, available_count = slot_with_count
            
            return SlotResponse(
                id=slot.id,
                resource_id=slot.resource_id,
                start_time=slot.start_time,
                end_time=slot.end_time,
                version=slot.version
            )
            
        except Exception as e:
            logger.error(f"Error fetching slot availability {slot_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch slot availability"
            )
            
    @staticmethod
    def get_resources_by_type(db: Session, resource_type: str) -> List[ResourceResponse]:
        """Get resources by type"""
        logger.info(f"Fetching resources by type: {resource_type}")
        
        try:
            resources = db.query(Resource).filter(Resource.type == resource_type).all()
            
            logger.info(f"Found {len(resources)} resources of type: {resource_type}")
            
            return [ResourceResponse.model_validate(resource) for resource in resources]
            
        except Exception as e:
            logger.error(f"Error fetching resources by type {resource_type}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch resources by type"
            )
    
    @staticmethod
    def get_resource_types(db: Session) -> List[str]:
        """Get all available resource types"""
        logger.info("Fetching all resource types")
        
        try:
            types = db.query(Resource.type).distinct().all()
            type_list = [t[0] for t in types if t[0]]
            
            logger.info(f"Found {len(type_list)} resource types: {type_list}")
            
            return type_list
            
        except Exception as e:
            logger.error(f"Error fetching resource types: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch resource types"
            )