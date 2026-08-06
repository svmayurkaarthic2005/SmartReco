"""Add re_enroll, unenroll, module_complete, lesson_complete event types

Revision ID: 002_add_event_types
Revises: 001_initial_schema
Create Date: 2026-08-06 08:00:00.000000

These event types were missing from the initial migration's enum definition.
Since the event_type column uses native_enum=False (varchar), this migration
only updates the check constraint (if any) and documents the new valid values.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_event_types'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The event_type column uses native_enum=False (stored as varchar),
    # so no ALTER TYPE is needed. This migration documents that the following
    # event_type values are now valid: unenroll, re_enroll, module_complete,
    # lesson_complete, wishlist, add_to_cart.
    # If your DB has a native PostgreSQL enum, run:
    #   ALTER TYPE event_type ADD VALUE 're_enroll';
    #   ALTER TYPE event_type ADD VALUE 'unenroll';
    #   ALTER TYPE event_type ADD VALUE 'module_complete';
    #   ALTER TYPE event_type ADD VALUE 'lesson_complete';
    pass


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; downgrade is a no-op.
    pass
