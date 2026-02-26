"""add heritage email logs table

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'  # This should match your last migration
branch_labels = None
depends_on = None


def upgrade():
    # Create heritage_email_logs table
    op.create_table('heritage_email_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('message_id', sa.String(255), nullable=True, index=True),
        sa.Column('to_emails', sa.Text, nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('email_type', sa.String(50), nullable=False, server_default='general'),
        sa.Column('status', sa.String(50), nullable=False, server_default='sent'),
        sa.Column('html_content', sa.Text, nullable=True),
        sa.Column('text_content', sa.Text, nullable=True),
        sa.Column('attachments_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('invoice_amount', sa.Float, nullable=True),
        sa.Column('invoice_description', sa.Text, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes
    op.create_index('ix_heritage_email_logs_message_id', 'heritage_email_logs', ['message_id'])
    op.create_index('ix_heritage_email_logs_status', 'heritage_email_logs', ['status'])
    op.create_index('ix_heritage_email_logs_email_type', 'heritage_email_logs', ['email_type'])
    op.create_index('ix_heritage_email_logs_created_at', 'heritage_email_logs', ['created_at'])
    
    # Create conditional index for invoice lookups
    op.create_index('ix_heritage_email_logs_invoice', 'heritage_email_logs', ['invoice_number'], 
                    postgresql_where=sa.text('invoice_number IS NOT NULL'))


def downgrade():
    # Drop indexes
    op.drop_index('ix_heritage_email_logs_invoice', table_name='heritage_email_logs')
    op.drop_index('ix_heritage_email_logs_created_at', table_name='heritage_email_logs')
    op.drop_index('ix_heritage_email_logs_email_type', table_name='heritage_email_logs')
    op.drop_index('ix_heritage_email_logs_status', table_name='heritage_email_logs')
    op.drop_index('ix_heritage_email_logs_message_id', table_name='heritage_email_logs')
    
    # Drop table
    op.drop_table('heritage_email_logs')