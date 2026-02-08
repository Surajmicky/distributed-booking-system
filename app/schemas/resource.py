# app/schemas/resource.py
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

class ResourceBase(BaseModel):
    name: str
    type: str
    meta_data: Dict[str, Any]

class ResourceCreate(ResourceBase):
    pass

class ResourceResponse(ResourceBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class SlotBase(BaseModel):
    start_time: datetime
    end_time: datetime
    capacity: int

class SlotResponse(SlotBase):
    id: UUID
    resource_id: UUID
    version: int
    
    class Config:
        from_attributes = True

class ResourceWithSlots(ResourceResponse):
    slots: List[SlotResponse] = []

class ResourceListResponse(BaseModel):
    resources: List[ResourceResponse]
    total: int
    page: int
    size: int