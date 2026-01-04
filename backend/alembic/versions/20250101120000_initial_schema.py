"""Initial schema

Revision ID: 20250101120000
Revises: 
Create Date: 2025-01-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250101120000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create uuid-ossp extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create enums
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'responsible', 'viewer')")
    op.execute("CREATE TYPE project_status AS ENUM ('active', 'archived', 'on_hold')")
    op.execute("CREATE TYPE item_status AS ENUM ('draft', 'in_progress', 'completed', 'cancelled')")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'responsible', 'viewer', name='user_role', create_type=False), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'archived', 'on_hold', name='project_status', create_type=False), nullable=False, server_default='active'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create items table
    op.create_table(
        'items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('part_number', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'in_progress', 'completed', 'cancelled', name='item_status', create_type=False), nullable=False, server_default='draft'),
        sa.Column('current_progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('docs_completion_percent', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('current_progress >= 0 AND current_progress <= 100', name='check_current_progress'),
        sa.CheckConstraint('docs_completion_percent >= 0 AND docs_completion_percent <= 100', name='check_docs_completion_percent'),
    )
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('type', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create document_revisions table
    op.create_table(
        'document_revisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('revision_label', sa.String(10), nullable=False),
        sa.Column('file_storage_uuid', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('change_note', sa.Text(), nullable=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
    )
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('event_payload', postgresql.JSONB(), nullable=True),
    )
    
    # Create progress_history table
    op.create_table(
        'progress_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('old_progress', sa.Integer(), nullable=False),
        sa.Column('new_progress', sa.Integer(), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('comment', sa.Text(), nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_items_project', 'items', ['project_id'])
    op.create_index('idx_items_responsible', 'items', ['responsible_id'])
    op.create_index('idx_items_part_number', 'items', ['part_number'])
    op.create_index('idx_documents_item', 'documents', ['item_id'])
    op.create_index('idx_revisions_document', 'document_revisions', ['document_id'])
    op.create_index('idx_revisions_storage_uuid', 'document_revisions', ['file_storage_uuid'])
    
    # Create partial unique index for is_current
    op.execute('CREATE UNIQUE INDEX ux_doc_current_rev ON document_revisions(document_id) WHERE (is_current = true)')
    
    op.create_index('idx_audit_timestamp', 'audit_log', [sa.text('timestamp DESC')])
    op.create_index('idx_audit_user', 'audit_log', ['user_id'])
    op.create_index('idx_audit_action', 'audit_log', ['action_type'])
    
    # Create partial index for unread notifications
    op.execute('CREATE INDEX idx_notifications_user_unread ON notifications(user_id) WHERE (read_at IS NULL)')
    
    op.create_index('idx_progress_history_item', 'progress_history', ['item_id', sa.text('changed_at DESC')])


def downgrade() -> None:
    # Drop indexes
    op.execute('DROP INDEX IF EXISTS idx_progress_history_item')
    op.execute('DROP INDEX IF EXISTS idx_notifications_user_unread')
    op.execute('DROP INDEX IF EXISTS idx_audit_action')
    op.execute('DROP INDEX IF EXISTS idx_audit_user')
    op.execute('DROP INDEX IF EXISTS idx_audit_timestamp')
    op.execute('DROP INDEX IF EXISTS ux_doc_current_rev')
    op.execute('DROP INDEX IF EXISTS idx_revisions_storage_uuid')
    op.execute('DROP INDEX IF EXISTS idx_revisions_document')
    op.execute('DROP INDEX IF EXISTS idx_documents_item')
    op.execute('DROP INDEX IF EXISTS idx_items_part_number')
    op.execute('DROP INDEX IF EXISTS idx_items_responsible')
    op.execute('DROP INDEX IF EXISTS idx_items_project')
    
    # Drop tables
    op.drop_table('progress_history')
    op.drop_table('notifications')
    op.drop_table('audit_log')
    op.drop_table('document_revisions')
    op.drop_table('documents')
    op.drop_table('items')
    op.drop_table('projects')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS item_status')
    op.execute('DROP TYPE IF EXISTS project_status')
    op.execute('DROP TYPE IF EXISTS user_role')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')

