# app/services/resource_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status
from app.models.resource import Resource
from app.models.slot import Slot
from app.schemas.resource import ResourceResponse, ResourceWithSlots, SlotResponse, ResourceListResponse
from app.core.logging import logger
from app.models.booking import Booking


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
            
            # Get all slots that meet the time criteria
            all_slots = query.order_by(Slot.start_time).all()
            
            # Filter out booked slots
            available_slots = []
            for slot in all_slots:
                # Check if slot is already booked
                existing_booking = db.query(Booking).filter(
                    Booking.slot_id == slot.id,
                    Booking.status == "confirmed"
                ).first()
                
                if not existing_booking:
                    available_slots.append(slot)
            
            logger.info(f"Found {len(all_slots)} total slots, {len(available_slots)} available for resource {resource_id}")
            
            return ResourceWithSlots(
                id=resource.id,
                name=resource.name,
                type=resource.type,
                meta_data=resource.meta_data,
                created_at=resource.created_at,
                slots=[SlotResponse.model_validate(slot) for slot in available_slots]
            )
            
        except Exception as e:
            logger.error(f"Error fetching resource with slots {resource_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch resource with slots"
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