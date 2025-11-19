"""Add email provider and attachment fields to campaigns

Revision ID: 20251118_provider_fields
Revises: 20251114_email_system
Create Date: 2025-11-18 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251118_provider_fields'
down_revision = '20251114_email_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email provider configuration fields
    op.add_column('email_campaigns', sa.Column('email_provider', sa.String(50), nullable=False, server_default='smtp'))
    op.add_column('email_campaigns', sa.Column('smtp_host', sa.String(255), nullable=True))
    op.add_column('email_campaigns', sa.Column('smtp_port', sa.Integer(), nullable=True))
    op.add_column('email_campaigns', sa.Column('smtp_username', sa.String(255), nullable=True))
    op.add_column('email_campaigns', sa.Column('smtp_password', sa.String(255), nullable=True))
    
    # Add attachments field
    op.add_column('email_campaigns', sa.Column('attachments', sa.JSON(), nullable=True))
    
    # Add attachments to email_queue
    op.add_column('email_queue', sa.Column('attachments', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove columns
    op.drop_column('email_queue', 'attachments')
    op.drop_column('email_campaigns', 'attachments')
    op.drop_column('email_campaigns', 'smtp_password')
    op.drop_column('email_campaigns', 'smtp_username')
    op.drop_column('email_campaigns', 'smtp_port')
    op.drop_column('email_campaigns', 'smtp_host')
    op.drop_column('email_campaigns', 'email_provider')

