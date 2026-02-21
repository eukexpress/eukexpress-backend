# Eukexpress\backend\migrations\versions\001_initial_migration.py
"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create admin table
    op.create_table(
        'admin',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('last_login_ip', sa.String(45)),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_admin_username', 'admin', ['username'])
    op.create_index('ix_admin_email', 'admin', ['email'])
    
    # Create shipments table
    op.create_table(
        'shipments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        
        # TRACKING INFORMATION
        sa.Column('tracking_number', sa.String(8), unique=True, nullable=False),
        sa.Column('invoice_number', sa.String(50), unique=True, nullable=False),
        
        # SENDER INFORMATION
        sa.Column('sender_name', sa.String(255), nullable=False),
        sa.Column('sender_email', sa.String(255), nullable=False),
        sa.Column('sender_phone', sa.String(50), nullable=False),
        sa.Column('sender_address', sa.Text, nullable=False),
        
        # RECIPIENT INFORMATION
        sa.Column('recipient_name', sa.String(255), nullable=False),
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('recipient_phone', sa.String(50), nullable=False),
        sa.Column('recipient_address', sa.Text, nullable=False),
        
        # SHIPMENT DETAILS
        sa.Column('origin_location', sa.String(255), nullable=False),
        sa.Column('origin_code', sa.String(10)),
        sa.Column('destination_location', sa.String(255), nullable=False),
        sa.Column('destination_code', sa.String(10)),
        sa.Column('goods_description', sa.Text, nullable=False),
        sa.Column('weight_kg', sa.DECIMAL(10, 2)),
        sa.Column('dimensions', sa.JSON),
        sa.Column('declared_value', sa.DECIMAL(12, 2)),
        sa.Column('declared_currency', sa.String(3), server_default='USD'),
        
        # IMAGES
        sa.Column('front_image_path', sa.String(500), nullable=False),
        sa.Column('rear_image_path', sa.String(500), nullable=False),
        sa.Column('front_image_hash', sa.String(64), nullable=False),
        sa.Column('rear_image_hash', sa.String(64), nullable=False),
        
        # PAYMENT INFORMATION
        sa.Column('shipping_amount', sa.DECIMAL(12, 2), nullable=False),
        sa.Column('payment_currency', sa.String(3), server_default='NGN'),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('payment_status', sa.String(20), server_default='PENDING'),
        sa.Column('payment_received_at', sa.DateTime(timezone=True)),
        
        # DATES
        sa.Column('sending_date', sa.Date, nullable=False),
        sa.Column('estimated_delivery_date', sa.Date, nullable=False),
        sa.Column('actual_delivery_date', sa.Date),
        
        # STATUS
        sa.Column('current_status', sa.String(50), nullable=False, server_default='BOOKED'),
        sa.Column('current_location', sa.String(255)),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # INTERNATIONAL FLAG
        sa.Column('is_international', sa.Boolean, server_default='false'),
        
        # CUSTOMS BOND
        sa.Column('customs_bond_active', sa.Boolean, server_default='false'),
        sa.Column('customs_bond_activated_at', sa.DateTime(timezone=True)),
        sa.Column('customs_bond_released_at', sa.DateTime(timezone=True)),
        sa.Column('customs_bond_location', sa.String(255)),
        sa.Column('customs_bond_reference', sa.String(100)),
        sa.Column('customs_bond_notes', sa.Text),
        
        # SECURITY HOLD
        sa.Column('security_hold_active', sa.Boolean, server_default='false'),
        sa.Column('security_hold_activated_at', sa.DateTime(timezone=True)),
        sa.Column('security_hold_cleared_at', sa.DateTime(timezone=True)),
        sa.Column('security_hold_location', sa.String(255)),
        sa.Column('security_hold_reference', sa.String(100)),
        sa.Column('security_hold_notes', sa.Text),
        
        # CARGO DAMAGE
        sa.Column('damage_reported', sa.Boolean, server_default='false'),
        sa.Column('damage_reported_at', sa.DateTime(timezone=True)),
        sa.Column('damage_resolved_at', sa.DateTime(timezone=True)),
        sa.Column('damage_description', sa.Text),
        sa.Column('damage_resolution_notes', sa.Text),
        
        # RETURN TO SENDER
        sa.Column('return_active', sa.Boolean, server_default='false'),
        sa.Column('return_initiated_at', sa.DateTime(timezone=True)),
        sa.Column('return_completed_at', sa.DateTime(timezone=True)),
        sa.Column('return_reason', sa.Text),
        
        # DELAY
        sa.Column('delay_active', sa.Boolean, server_default='false'),
        sa.Column('delay_reported_at', sa.DateTime(timezone=True)),
        sa.Column('delay_resolved_at', sa.DateTime(timezone=True)),
        sa.Column('delay_reason', sa.Text),
        sa.Column('delay_notes', sa.Text),
        sa.Column('original_eta', sa.Date),
        sa.Column('revised_eta', sa.Date),
        
        # METADATA
        sa.Column('qr_code_path', sa.String(500)),
        sa.Column('invoice_pdf_path', sa.String(500)),
        sa.Column('created_by_admin', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes for shipments
    op.create_index('ix_shipments_tracking', 'shipments', ['tracking_number'])
    op.create_index('ix_shipments_status', 'shipments', ['current_status'])
    op.create_index('ix_shipments_dates', 'shipments', ['sending_date', 'estimated_delivery_date'])
    op.create_index('ix_shipments_customs_active', 'shipments', ['customs_bond_active'], postgresql_where=sa.text('customs_bond_active = true'))
    op.create_index('ix_shipments_delay_active', 'shipments', ['delay_active'], postgresql_where=sa.text('delay_active = true'))
    op.create_index('ix_shipments_damage_reported', 'shipments', ['damage_reported'], postgresql_where=sa.text('damage_reported = true'))
    
    # Create status_history table
    op.create_table(
        'status_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('shipment_id', UUID(as_uuid=True), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('previous_status', sa.String(50)),
        sa.Column('new_status', sa.String(50), nullable=False),
        sa.Column('changed_by', sa.String(50), server_default='admin'),
        sa.Column('location', sa.String(255)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_status_history_shipment', 'status_history', ['shipment_id', 'created_at'])
    
    # Create intervention_log table
    op.create_table(
        'intervention_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('shipment_id', UUID(as_uuid=True), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('intervention_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('previous_state', sa.Boolean),
        sa.Column('new_state', sa.Boolean),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create email_log table
    op.create_table(
        'email_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('shipment_id', UUID(as_uuid=True), sa.ForeignKey('shipments.id', ondelete='SET NULL')),
        sa.Column('recipient_type', sa.String(20)),
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('email_type', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('message_id', sa.String(255)),
        sa.Column('status', sa.String(20), server_default='SENT'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_email_log_shipment', 'email_log', ['shipment_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('email_log')
    op.drop_table('intervention_log')
    op.drop_table('status_history')
    op.drop_table('shipments')
    op.drop_table('admin')