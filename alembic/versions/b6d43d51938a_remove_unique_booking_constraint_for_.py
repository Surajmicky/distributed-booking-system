"""remove unique booking constraint for capacity-based booking

Revision ID: b6d43d51938a
Revises: a909c535ea77
Create Date: 2026-02-10 08:11:36.366220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6d43d51938a'
down_revision: Union[str, Sequence[str], None] = 'a909c535ea77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop the old constraint
    op.execute("DROP INDEX IF EXISTS one_active_booking;")

def downgrade():
    # Recreate old constraint if needed
    op.execute("""
    CREATE UNIQUE INDEX one_active_booking
    ON bookings(slot_id)
    WHERE status = 'confirmed';
    """)
