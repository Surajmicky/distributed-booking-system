"""populate seats for existing slots

Revision ID: c880d8688ab4
Revises: daa6e5425bed
Create Date: 2026-02-10 09:11:02.745985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4


# revision identifiers, used by Alembic.
revision: str = 'c880d8688ab4'
down_revision: Union[str, Sequence[str], None] = 'daa6e5425bed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Get database connection
    connection = op.get_bind()
    session = Session(bind=connection)
    
    try:
        # Get all slots with their resource capacity from meta_data
        result = session.execute(text("""
            SELECT s.id, r.meta_data
            FROM slots s
            JOIN resources r ON s.resource_id = r.id
        """))
        
        slots = result.fetchall()
        
        for slot_id, meta_data in slots:
            # Parse capacity from meta_data JSON
            import json
            try:
                if meta_data:
                    resource_data = json.loads(meta_data)
                    capacity = resource_data.get('capacity', 10)  # Default to 10 if not found
                else:
                    capacity = 10
            except (json.JSONDecodeError, TypeError):
                capacity = 10  # Default if meta_data is invalid
            
            # Create seats for each slot
            for seat_num in range(1, capacity + 1):
                seat_number = f"S{seat_num:02d}"  # S01, S02, etc.
                
                session.execute(text("""
                    INSERT INTO seats (id, slot_id, seat_number, status, seat_type, created_at, updated_at)
                    VALUES (:seat_id, :slot_id, :seat_number, 'available', 'standard', NOW(), NOW())
                """), {
                    'seat_id': str(uuid4()),
                    'slot_id': str(slot_id),
                    'seat_number': seat_number
                })
        
        session.commit()
        print(f"Created seats for {len(slots)} slots using resource meta_data capacity")
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def downgrade() -> None:
    """Downgrade schema."""
    # Remove all created seats
    connection = op.get_bind()
    session = Session(bind=connection)
    
    try:
        session.execute(text("DELETE FROM seats"))
        session.commit()
        print("Removed all seats")
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
