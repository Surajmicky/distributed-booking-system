# app/api/v1/resources.py
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.services.resource import ResourceService
from app.schemas.resource import ResourceResponse, ResourceWithSlots, ResourceListResponse
from app.core.logging import logger

router = APIRouter(prefix="/resources", tags=["resources"])

@router.get("/", response_model=ResourceListResponse)
def get_all_resources(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    type: Optional[str] = Query(None, description="Filter by resource type"),
    db: Session = Depends(get_db)
):
    """Get all resources with pagination and optional type filter"""
    logger.info(f"API request: GET /resources/ - skip={skip}, limit={limit}, type={type}")
    
    try:
        return ResourceService.get_all_resources(db, skip=skip, limit=limit, resource_type=type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_all_resources: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/types", response_model=List[str])
def get_resource_types(db: Session = Depends(get_db)):
    """Get all available resource types"""
    logger.info("API request: GET /resources/types")
    
    try:
        return ResourceService.get_resource_types(db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_resource_types: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(resource_id: UUID, db: Session = Depends(get_db)):
    """Get a specific resource by ID"""
    logger.info(f"API request: GET /resources/{resource_id}")
    
    try:
        resource = ResourceService.get_resource_by_id(db, resource_id)
        if not resource:
            logger.warning(f"Resource not found in API: {resource_id}")
            raise HTTPException(status_code=404, detail="Resource not found")
        return resource
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_resource: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/{resource_id}/slots", response_model=ResourceWithSlots)
def get_resource_with_slots(
    resource_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Filter slots from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter slots until this date"),
    db: Session = Depends(get_db)
):
    """Get a resource with its available slots"""
    logger.info(f"API request: GET /resources/{resource_id}/slots - start_date={start_date}, end_date={end_date}")
    
    try:
        resource_with_slots = ResourceService.get_resource_with_slots(
            db, resource_id, start_date, end_date
        )
        if not resource_with_slots:
            logger.warning(f"Resource not found for slots API: {resource_id}")
            raise HTTPException(status_code=404, detail="Resource not found")
        return resource_with_slots
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_resource_with_slots: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )