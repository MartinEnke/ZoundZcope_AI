"""Add reference_track_id to sessions

Revision ID: 8d85c4c70039
Revises: 7a38404fc5c7
Create Date: 2025-07-22 14:19:58.794827

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d85c4c70039'
down_revision = '7a38404fc5c7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sessions', sa.Column('reference_track_id', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_sessions_reference_track_id_tracks',
        'sessions',
        'tracks',
        ['reference_track_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_sessions_reference_track_id_tracks', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'reference_track_id')