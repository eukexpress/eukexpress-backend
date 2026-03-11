"""Add email schemas and intervention fields

Revision ID: a009247a80ea
Revises: 001
Create Date: 2026-03-11 09:07:41.529677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision: str = 'a009247a80ea'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================================================
    # SAFELY HANDLE heritage_email_logs - ONLY IF IT EXISTS
    # =====================================================
    conn = op.get_bind()
    
    # Check if heritage_email_logs table exists before trying to drop it
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'heritage_email_logs')"
    )).scalar()
    
    if result:
        # Drop index first if it exists
        op.execute("DROP INDEX IF EXISTS ix_heritage_email_logs_message_id")
        # Drop the table
        op.drop_table('heritage_email_logs')
        print("✓ Dropped heritage_email_logs table")
    else:
        print("✓ heritage_email_logs table does not exist, skipping...")
    
    # =====================================================
    # FIX ADMIN TABLE - Preserve existing data
    # =====================================================
    
    # Safely handle indexes - drop if they exist, recreate properly
    op.execute("DROP INDEX IF EXISTS ix_admin_email")
    op.execute("DROP INDEX IF EXISTS ix_admin_username")
    
    # Recreate indexes with proper names
    op.create_index(op.f('ix_admin_email'), 'admin', ['email'], unique=True)
    op.create_index(op.f('ix_admin_username'), 'admin', ['username'], unique=True)
    
    # =====================================================
    # FIX EMAIL LOG TABLE - Add missing columns if needed
    # =====================================================
    
    # Check if bulk_email_campaigns table exists, if not create it
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'bulk_email_campaigns')"
    )).scalar()
    
    if not result:
        # Create bulk_email_campaigns table
        op.create_table(
            'bulk_email_campaigns',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('campaign_name', sa.String(255)),
            sa.Column('recipient_filter', sa.String(50)),
            sa.Column('subject', sa.String(500), nullable=False),
            sa.Column('message', sa.Text, nullable=False),
            sa.Column('recipient_count', sa.Integer),
            sa.Column('sent_by', UUID(as_uuid=True), sa.ForeignKey('admin.id')),
            sa.Column('status', sa.String(20), server_default='PENDING'),
            sa.Column('error_message', sa.Text),
            sa.Column('completed_at', sa.DateTime(timezone=True)),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        )
        print("✓ Created bulk_email_campaigns table")
    
    # Fix email_log indexes
    op.execute("DROP INDEX IF EXISTS ix_email_log_shipment")
    op.create_index(op.f('ix_email_log_created_at'), 'email_log', ['created_at'], unique=False)
    
    # =====================================================
    # FIX SHIPMENTS TABLE - Add missing indexes
    # =====================================================
    
    # Drop old indexes if they exist
    op.execute("DROP INDEX IF EXISTS ix_shipments_tracking")
    op.execute("DROP INDEX IF EXISTS ix_shipments_status")
    op.execute("DROP INDEX IF EXISTS ix_shipments_dates")
    op.execute("DROP INDEX IF EXISTS ix_shipments_customs_active")
    op.execute("DROP INDEX IF EXISTS ix_shipments_delay_active")
    op.execute("DROP INDEX IF EXISTS ix_shipments_damage_reported")
    op.execute("DROP INDEX IF EXISTS ix_shipments_customs_active_2")
    op.execute("DROP INDEX IF EXISTS ix_shipments_damage_reported_2")
    
    # Create new standardized indexes
    op.create_index(op.f('ix_shipments_tracking_number'), 'shipments', ['tracking_number'], unique=True)
    op.create_index(op.f('ix_shipments_current_status'), 'shipments', ['current_status'], unique=False)
    op.create_index(op.f('ix_shipments_customs_bond_active'), 'shipments', ['customs_bond_active'], unique=False)
    op.create_index(op.f('ix_shipments_security_hold_active'), 'shipments', ['security_hold_active'], unique=False)
    op.create_index(op.f('ix_shipments_damage_reported'), 'shipments', ['damage_reported'], unique=False)
    op.create_index(op.f('ix_shipments_return_active'), 'shipments', ['return_active'], unique=False)
    op.create_index(op.f('ix_shipments_delay_active'), 'shipments', ['delay_active'], unique=False)
    
    # =====================================================
    # FIX STATUS HISTORY TABLE
    # =====================================================
    
    op.execute("DROP INDEX IF EXISTS ix_status_history_shipment")
    op.create_index(op.f('ix_status_history_created_at'), 'status_history', ['created_at'], unique=False)
    
    print("✓ Migration completed successfully")


def downgrade() -> None:
    """Downgrade to previous version - REVERSES all changes above"""
    
    # =====================================================
    # REVERSE STATUS HISTORY CHANGES
    # =====================================================
    op.execute("DROP INDEX IF EXISTS ix_status_history_created_at")
    op.create_index('ix_status_history_shipment', 'status_history', ['shipment_id', 'created_at'], unique=False)
    
    # =====================================================
    # REVERSE SHIPMENTS INDEX CHANGES
    # =====================================================
    op.execute("DROP INDEX IF EXISTS ix_shipments_tracking_number")
    op.execute("DROP INDEX IF EXISTS ix_shipments_current_status")
    op.execute("DROP INDEX IF EXISTS ix_shipments_customs_bond_active")
    op.execute("DROP INDEX IF EXISTS ix_shipments_security_hold_active")
    op.execute("DROP INDEX IF EXISTS ix_shipments_damage_reported")
    op.execute("DROP INDEX IF EXISTS ix_shipments_return_active")
    op.execute("DROP INDEX IF EXISTS ix_shipments_delay_active")
    
    # Restore original indexes
    op.create_index('ix_shipments_tracking', 'shipments', ['tracking_number'], unique=False)
    op.create_index('ix_shipments_status', 'shipments', ['current_status'], unique=False)
    op.create_index('ix_shipments_dates', 'shipments', ['sending_date', 'estimated_delivery_date'], unique=False)
    op.create_index('ix_shipments_customs_active', 'shipments', ['customs_bond_active'], unique=False, postgresql_where=sa.text('customs_bond_active = true'))
    op.create_index('ix_shipments_delay_active', 'shipments', ['delay_active'], unique=False, postgresql_where=sa.text('delay_active = true'))
    op.create_index('ix_shipments_damage_reported', 'shipments', ['damage_reported'], unique=False, postgresql_where=sa.text('damage_reported = true'))
    
    # =====================================================
    # REVERSE EMAIL LOG CHANGES
    # =====================================================
    op.execute("DROP INDEX IF EXISTS ix_email_log_created_at")
    op.create_index('ix_email_log_shipment', 'email_log', ['shipment_id', 'created_at'], unique=False)
    
    # Drop bulk_email_campaigns table if we created it
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'bulk_email_campaigns')"
    )).scalar()
    
    if result:
        op.drop_table('bulk_email_campaigns')
    
    # =====================================================
    # REVERSE ADMIN INDEX CHANGES
    # =====================================================
    op.execute("DROP INDEX IF EXISTS ix_admin_email")
    op.execute("DROP INDEX IF EXISTS ix_admin_username")
    
    # Restore original admin indexes
    op.create_index('ix_admin_email', 'admin', ['email'], unique=False)
    op.create_index('ix_admin_username', 'admin', ['username'], unique=False)
    
    # =====================================================
    # RESTORE heritage_email_logs IF IT WAS DROPPED
    # =====================================================
    # Check if we dropped it in upgrade
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'heritage_email_logs')"
    )).scalar()
    
    if not result:
        # Recreate heritage_email_logs table
        op.create_table('heritage_email_logs',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('message_id', sa.String(255)),
            sa.Column('to_emails', sa.Text, nullable=False),
            sa.Column('subject', sa.String(255), nullable=False),
            sa.Column('email_type', sa.String(50), nullable=False),
            sa.Column('status', sa.String(50), nullable=False),
            sa.Column('html_content', sa.Text),
            sa.Column('text_content', sa.Text),
            sa.Column('attachments_count', sa.Integer),
            sa.Column('invoice_number', sa.String(100)),
            sa.Column('invoice_amount', sa.Float),
            sa.Column('error_message', sa.Text),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(timezone=True)),
            sa.PrimaryKeyConstraint('id', name='heritage_email_logs_pkey')
        )
        op.create_index('ix_heritage_email_logs_message_id', 'heritage_email_logs', ['message_id'], unique=False)
    
    print("✓ Downgrade completed")