"""Add tech documents

Revision ID: 20250103120000
Revises: 20250102120000
Create Date: 2025-01-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250103120000'
down_revision: Union[str, None] = '20250102120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tech_documents table
    op.create_table(
        'tech_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project_sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_extension', sa.String(10), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )

    # Create tech_document_versions table
    op.create_table(
        'tech_document_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tech_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('storage_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_extension', sa.String(10), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
    )

    # Create indexes
    op.create_index('idx_tech_documents_section', 'tech_documents', ['section_id'])
    op.create_index('idx_tech_documents_storage_uuid', 'tech_documents', ['storage_uuid'])
    op.create_index('idx_tech_versions_document', 'tech_document_versions', ['document_id'])
    op.create_index('idx_tech_versions_storage_uuid', 'tech_document_versions', ['storage_uuid'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_tech_versions_storage_uuid', table_name='tech_document_versions')
    op.drop_index('idx_tech_versions_document', table_name='tech_document_versions')
    op.drop_index('idx_tech_documents_storage_uuid', table_name='tech_documents')
    op.drop_index('idx_tech_documents_section', table_name='tech_documents')

    # Drop tables
    op.drop_table('tech_document_versions')
    op.drop_table('tech_documents')
