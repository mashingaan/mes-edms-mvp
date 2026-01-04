"""Add project sections

Revision ID: 20250102120000
Revises: 20250101120002
Create Date: 2025-01-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250102120000'
down_revision: Union[str, None] = '20250101120002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project_sections table
    op.create_table(
        'project_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('project_id', 'code', name='uq_project_section_code'),
    )
    
    # Create index on project_id for performance
    op.create_index('idx_sections_project', 'project_sections', ['project_id'])
    
    # Add section_id column to items table (nullable)
    op.add_column('items', sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_items_section_id',
        'items',
        'project_sections',
        ['section_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create index on section_id for performance
    op.create_index('idx_items_section', 'items', ['section_id'])


def downgrade() -> None:
    # Drop index on section_id
    op.drop_index('idx_items_section', table_name='items')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_items_section_id', 'items', type_='foreignkey')
    
    # Drop section_id column from items
    op.drop_column('items', 'section_id')
    
    # Drop index on project_sections
    op.drop_index('idx_sections_project', table_name='project_sections')
    
    # Drop project_sections table
    op.drop_table('project_sections')

