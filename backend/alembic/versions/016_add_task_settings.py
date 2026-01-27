"""Add task settings columns to app_settings

Revision ID: 016
Revises: 015
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '016'
down_revision: Union[str, None] = '015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add task 3 & 4 prompts, per-task attributes, and length settings."""
    # Task 3 & 4 prompts
    op.add_column('app_settings', sa.Column('default_task3_prompt', sa.Text(), nullable=True))
    op.add_column('app_settings', sa.Column('default_task4_prompt', sa.Text(), nullable=True))

    # Per-task attribute settings (JSON arrays)
    op.add_column('app_settings', sa.Column('task1_default_attributes', sa.JSON(), nullable=True))
    op.add_column('app_settings', sa.Column('task1_mandatory_attributes', sa.JSON(), nullable=True))
    op.add_column('app_settings', sa.Column('task2_default_attributes', sa.JSON(), nullable=True))
    op.add_column('app_settings', sa.Column('task2_mandatory_attributes', sa.JSON(), nullable=True))
    op.add_column('app_settings', sa.Column('task3_default_attributes', sa.JSON(), nullable=True))
    op.add_column('app_settings', sa.Column('task3_mandatory_attributes', sa.JSON(), nullable=True))
    op.add_column('app_settings', sa.Column('task4_default_attributes', sa.JSON(), nullable=True))
    op.add_column('app_settings', sa.Column('task4_mandatory_attributes', sa.JSON(), nullable=True))

    # Length settings for Task 1 (title generation)
    op.add_column('app_settings', sa.Column('task1_min_length', sa.Integer(), nullable=True))
    op.add_column('app_settings', sa.Column('task1_max_length', sa.Integer(), nullable=True))
    op.add_column('app_settings', sa.Column('task1_target_length', sa.Integer(), nullable=True))

    # Length settings for Task 2 (description generation)
    op.add_column('app_settings', sa.Column('task2_min_length', sa.Integer(), nullable=True))
    op.add_column('app_settings', sa.Column('task2_max_length', sa.Integer(), nullable=True))
    op.add_column('app_settings', sa.Column('task2_target_length', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove task settings columns."""
    # Length settings
    op.drop_column('app_settings', 'task2_target_length')
    op.drop_column('app_settings', 'task2_max_length')
    op.drop_column('app_settings', 'task2_min_length')
    op.drop_column('app_settings', 'task1_target_length')
    op.drop_column('app_settings', 'task1_max_length')
    op.drop_column('app_settings', 'task1_min_length')

    # Attribute settings
    op.drop_column('app_settings', 'task4_mandatory_attributes')
    op.drop_column('app_settings', 'task4_default_attributes')
    op.drop_column('app_settings', 'task3_mandatory_attributes')
    op.drop_column('app_settings', 'task3_default_attributes')
    op.drop_column('app_settings', 'task2_mandatory_attributes')
    op.drop_column('app_settings', 'task2_default_attributes')
    op.drop_column('app_settings', 'task1_mandatory_attributes')
    op.drop_column('app_settings', 'task1_default_attributes')

    # Prompts
    op.drop_column('app_settings', 'default_task4_prompt')
    op.drop_column('app_settings', 'default_task3_prompt')
