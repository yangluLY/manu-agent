"""rename machine modal to model

Revision ID: e1859c60e5ea
Revises: e53d81dd9ab2
Create Date: 2026-09-14 16:19:08.976961

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e1859c60e5ea'
down_revision: Union[str, Sequence[str], None] = 'e53d81dd9ab2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "machines",
        "modal",
        new_column_name="model",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "machines",
        "model",
        new_column_name="modal",
    )
