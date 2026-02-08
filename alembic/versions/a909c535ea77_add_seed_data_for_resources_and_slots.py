"""Add seed data for resources and slots

Revision ID: a909c535ea77
Revises: d83a240d58b7
Create Date: 2026-02-08 12:09:22.729779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import uuid
import json

# revision identifiers, used by Alembic.
revision: str = 'a909c535ea77'
down_revision: Union[str, Sequence[str], None] = 'd83a240d58b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    """Add seed data for resources and slots"""
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Check if seed data already exists
        existing_count = session.execute(sa.text("SELECT COUNT(*) FROM resources")).scalar()
        if existing_count > 0:
            print("Seed data already exists, skipping...")
            return
            
        # Create resources
        resources_data = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Conference Room A',
                'type': 'meeting_room',
                'meta_data': json.dumps({
                    "location": "Floor 1",
                    "capacity": 10,
                    "equipment": ["projector", "whiteboard", "video_conference"]
                }),
                'capacity': 10,  # Store capacity separately
                'created_at': datetime.now(timezone.utc)
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Conference Room B', 
                'type': 'meeting_room',
                'meta_data': json.dumps({
                    "location": "Floor 2",
                    "capacity": 6,
                    "equipment": ["whiteboard", "video_conference"]
                }),
                'capacity': 6,  # Store capacity separately
                'created_at': datetime.now(timezone.utc)
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Tennis Court 1',
                'type': 'sports_facility', 
                'meta_data': json.dumps({
                    "location": "Outdoor Area",
                    "capacity": 4,
                    "equipment": ["tennis_rackets", "balls"]
                }),
                'capacity': 4,  # Store capacity separately
                'created_at': datetime.now(timezone.utc)
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Swimming Pool',
                'type': 'recreational',
                'meta_data': json.dumps({
                    "location": "Building A",
                    "capacity": 20,
                    "equipment": ["pool_lounge", "showers"]
                }),
                'capacity': 20,  # Store capacity separately
                'created_at': datetime.now(timezone.utc)
            }
        ]
        
        # Insert resources
        for resource_data in resources_data:
            session.execute(
                sa.text("""
                    INSERT INTO resources (id, name, type, meta_data, created_at)
                    VALUES (:id, :name, :type, :meta_data, :created_at)
                """),
                resource_data
            )
        
        # Create slots with timezone handling
        india_offset = timedelta(hours=5, minutes=30)
        user_timezone = timezone(india_offset)
        current_local_time = datetime.now(user_timezone)
        base_date_local = current_local_time.replace(hour=9, minute=0, second=0, microsecond=0)
        
        if current_local_time.hour >= 9:
            base_date_local += timedelta(days=1)
            
        slots_data = []
        for resource in resources_data:
            for day_offset in range(7):
                current_date_local = base_date_local + timedelta(days=day_offset)
                for hour_offset in range(9):
                    start_time_local = current_date_local + timedelta(hours=hour_offset)
                    end_time_local = start_time_local + timedelta(hours=1)
                    
                    current_time_local = datetime.now(user_timezone)
                    if day_offset == 0 and start_time_local <= current_time_local:
                        continue
                        
                    start_time_utc = start_time_local.astimezone(timezone.utc)
                    end_time_utc = end_time_local.astimezone(timezone.utc)
                    
                    slots_data.append({
                        'id': str(uuid.uuid4()),
                        'resource_id': resource['id'],
                        'start_time': start_time_utc,
                        'end_time': end_time_utc,
                        'capacity': resource['capacity'],  # Use separate capacity field
                        'version': 1
                    })
        
        # Insert slots
        for slot_data in slots_data:
            session.execute(
                sa.text("""
                    INSERT INTO slots (id, resource_id, start_time, end_time, capacity, version)
                    VALUES (:id, :resource_id, :start_time, :end_time, :capacity, :version)
                """),
                slot_data
            )
        
        session.commit()
        print(f"Created {len(resources_data)} resources and {len(slots_data)} slots")
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def downgrade():
    """Remove seed data"""
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Delete slots first (foreign key constraint)
        session.execute(sa.text("DELETE FROM slots"))
        
        # Delete resources
        session.execute(sa.text("DELETE FROM resources"))
        
        session.commit()
        print("Seed data removed")
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()