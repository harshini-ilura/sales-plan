"""Add email system tables for bulk sending and lead enrichment

Revision ID: 002_email_system
Revises: 001_initial
Create Date: 2025-11-14 14:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '002_email_system'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create email system tables"""

    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False, server_default='initial'),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('available_variables', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('is_default', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('usage_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_used_at', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for email_templates
    op.create_index('ix_email_templates_name', 'email_templates', ['name'])
    op.create_index('ix_email_templates_is_active', 'email_templates', ['is_active'])
    op.create_index('ix_email_templates_is_deleted', 'email_templates', ['is_deleted'])
    op.create_index('idx_template_type_active', 'email_templates', ['template_type', 'is_active'])

    # Create email_campaigns table
    op.create_table(
        'email_campaigns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('target_filters', sa.JSON(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('follow_up_enabled', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('follow_up_delay_days', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('follow_up_template_id', sa.Integer(), nullable=True),
        sa.Column('sender_name', sa.String(length=255), nullable=True),
        sa.Column('sender_email', sa.String(length=255), nullable=True),
        sa.Column('reply_to', sa.String(length=255), nullable=True),
        sa.Column('total_recipients', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('emails_sent', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('emails_delivered', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('emails_opened', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('emails_clicked', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('emails_failed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('emails_bounced', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('emails_replied', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('send_rate_limit', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ),
        sa.ForeignKeyConstraint(['follow_up_template_id'], ['email_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for email_campaigns
    op.create_index('ix_email_campaigns_status', 'email_campaigns', ['status'])
    op.create_index('ix_email_campaigns_is_deleted', 'email_campaigns', ['is_deleted'])
    op.create_index('idx_campaign_status_scheduled', 'email_campaigns', ['status', 'scheduled_at'])

    # Create email_queue table
    op.create_table(
        'email_queue',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('sender_email', sa.String(length=255), nullable=False),
        sa.Column('sender_name', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('email_type', sa.String(length=50), nullable=True, server_default='initial'),
        sa.Column('parent_email_id', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['email_campaigns.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['sales_leads.id'], ),
        sa.ForeignKeyConstraint(['parent_email_id'], ['email_queue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for email_queue
    op.create_index('ix_email_queue_campaign_id', 'email_queue', ['campaign_id'])
    op.create_index('ix_email_queue_lead_id', 'email_queue', ['lead_id'])
    op.create_index('ix_email_queue_recipient_email', 'email_queue', ['recipient_email'])
    op.create_index('ix_email_queue_scheduled_at', 'email_queue', ['scheduled_at'])
    op.create_index('ix_email_queue_status', 'email_queue', ['status'])
    op.create_index('ix_email_queue_provider_message_id', 'email_queue', ['provider_message_id'])
    op.create_index('ix_email_queue_is_deleted', 'email_queue', ['is_deleted'])
    op.create_index('idx_queue_status_scheduled', 'email_queue', ['status', 'scheduled_at'])
    op.create_index('idx_queue_campaign_status', 'email_queue', ['campaign_id', 'status'])
    op.create_index('idx_queue_lead', 'email_queue', ['lead_id'])
    op.create_index('idx_queue_provider_message', 'email_queue', ['provider_message_id'])

    # Create email_tracking table
    op.create_table(
        'email_tracking',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('provider_event_id', sa.String(length=255), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['email_campaigns.id'], ),
        sa.ForeignKeyConstraint(['email_id'], ['email_queue.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['sales_leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for email_tracking
    op.create_index('ix_email_tracking_campaign_id', 'email_tracking', ['campaign_id'])
    op.create_index('ix_email_tracking_email_id', 'email_tracking', ['email_id'])
    op.create_index('ix_email_tracking_lead_id', 'email_tracking', ['lead_id'])
    op.create_index('ix_email_tracking_event_type', 'email_tracking', ['event_type'])
    op.create_index('ix_email_tracking_event_timestamp', 'email_tracking', ['event_timestamp'])
    op.create_index('idx_tracking_campaign_event', 'email_tracking', ['campaign_id', 'event_type'])
    op.create_index('idx_tracking_email_event', 'email_tracking', ['email_id', 'event_type'])
    op.create_index('idx_tracking_event_time', 'email_tracking', ['event_type', 'event_timestamp'])
    op.create_index('idx_tracking_lead', 'email_tracking', ['lead_id'])


def downgrade() -> None:
    """Drop email system tables"""
    op.drop_table('email_tracking')
    op.drop_table('email_queue')
    op.drop_table('email_campaigns')
    op.drop_table('email_templates')
