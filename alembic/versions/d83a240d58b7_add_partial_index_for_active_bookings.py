"""add partial index for active bookings

Revision ID: d83a240d58b7
Revises: 8ae316fe391f
Create Date: 2026-02-07 13:53:45.329880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd83a240d58b7'
down_revision: Union[str, Sequence[str], None] = '8ae316fe391f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE UNIQUE INDEX one_active_booking
    ON bookings(user_id, slot_id)
    WHERE status = 'confirmed';
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS one_active_booking;")
