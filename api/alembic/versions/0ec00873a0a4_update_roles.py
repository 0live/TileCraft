"""Update_roles

Revision ID: 0ec00873a0a4
Revises: 8871bb5597cc
Create Date: 2025-03-01 15:24:47.302044

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0ec00873a0a4"
down_revision: Union[str, None] = "8871bb5597cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE 'MANAGE_TEAMS';")
    op.execute("ALTER TYPE userrole ADD VALUE 'MANAGE_ATLASES';")
    op.execute("ALTER TYPE userrole ADD VALUE 'LOAD_DATA';")
    op.execute("ALTER TYPE userrole ADD VALUE 'LOAD_ICONS';")


def downgrade() -> None:
    pass
