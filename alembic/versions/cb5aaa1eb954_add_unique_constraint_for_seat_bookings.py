"""add unique constraint for seat bookings

Revision ID: cb5aaa1eb954
Revises: c880d8688ab4
Create Date: 2026-02-10 09:47:20.383951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb5aaa1eb954'
down_revision: Union[str, Sequence[str], None] = 'c880d8688ab4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique constraint to prevent double booking of confirmed seats
    op.create_index(
        'idx_one_confirmed_booking_per_seat',
        'bookings',
        ['seat_id'],
        unique=True,
        postgresql_where=sa.text("status = 'confirmed'")
    )
    
    # Add enum constraints for data integrity
    op.execute("""
        ALTER TABLE seats 
        ADD CONSTRAINT chk_seat_status 
        CHECK (status IN ('available', 'booked', 'reserved', 'maintenance'))
    """)
    
    op.execute("""
        ALTER TABLE bookings 
        ADD CONSTRAINT chk_booking_status 
        CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed'))
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove constraints
    op.execute("ALTER TABLE seats DROP CONSTRAINT IF EXISTS chk_seat_status")
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS chk_booking_status")
    
    # Remove the unique constraint
    op.drop_index('idx_one_confirmed_booking_per_seat', table_name='bookings')
