"""add document soft delete fields

Revision ID: 20250101120002
Revises: 20250101120001
Create Date: 2025-01-01 12:00:02.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250101120002'
down_revision = '20250101120001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add soft delete columns to documents table
    op.add_column('documents', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('documents', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('documents', sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key for deleted_by
    op.create_foreign_key(
        'fk_documents_deleted_by_users',
        'documents',
        'users',
        ['deleted_by'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create partial index for optimizing non-deleted document queries
    op.create_index(
        'idx_documents_is_deleted',
        'documents',
        ['is_deleted'],
        postgresql_where=sa.text('is_deleted = FALSE')
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_documents_is_deleted', table_name='documents')
    
    # Drop foreign key
    op.drop_constraint('fk_documents_deleted_by_users', 'documents', type_='foreignkey')
    
    # Drop columns
    op.drop_column('documents', 'deleted_by')
    op.drop_column('documents', 'deleted_at')
    op.drop_column('documents', 'is_deleted')

