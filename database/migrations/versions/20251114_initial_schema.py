"""Initial schema with all tables, indexes, and constraints

Revision ID: 001_initial
Revises:
Create Date: 2025-11-14 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with indexes and constraints"""

    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('company_type', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('employee_size_min', sa.Integer(), nullable=True),
        sa.Column('employee_size_max', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for companies
    op.create_index('ix_companies_domain', 'companies', ['domain'])
    op.create_index('ix_companies_country', 'companies', ['country'])
    op.create_index('ix_companies_industry', 'companies', ['industry'])
    op.create_index('ix_companies_is_deleted', 'companies', ['is_deleted'])
    op.create_index('idx_company_location', 'companies', ['country', 'city'])
    op.create_index('idx_company_industry_country', 'companies', ['industry', 'country'])

    # Create sales_leads table
    op.create_table(
        'sales_leads',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('email_verified', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('phone_verified', sa.String(length=50), nullable=True),
        sa.Column('additional_emails', sa.JSON(), nullable=True),
        sa.Column('additional_phones', sa.JSON(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('company_domain', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False, server_default='apify'),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('actor_id', sa.String(length=100), nullable=True),
        sa.Column('run_id', sa.String(length=100), nullable=True),
        sa.Column('dataset_id', sa.String(length=100), nullable=True),
        sa.Column('enrichment_status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('enrichment_data', sa.JSON(), nullable=True),
        sa.Column('lead_score', sa.Integer(), nullable=True),
        sa.Column('lead_status', sa.String(length=50), nullable=True, server_default='new'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for sales_leads
    op.create_index('ix_sales_leads_email', 'sales_leads', ['email'])
    op.create_index('ix_sales_leads_phone', 'sales_leads', ['phone'])
    op.create_index('ix_sales_leads_company_domain', 'sales_leads', ['company_domain'])
    op.create_index('ix_sales_leads_country', 'sales_leads', ['country'])
    op.create_index('ix_sales_leads_source', 'sales_leads', ['source'])
    op.create_index('ix_sales_leads_is_deleted', 'sales_leads', ['is_deleted'])
    op.create_index('idx_provider_external', 'sales_leads', ['provider_name', 'external_id'])
    op.create_index('idx_lead_source_actor', 'sales_leads', ['source', 'actor_id'])
    op.create_index('idx_lead_location', 'sales_leads', ['country', 'city'])
    op.create_index('idx_lead_status', 'sales_leads', ['lead_status', 'enrichment_status'])
    op.create_index('idx_lead_company', 'sales_leads', ['company_id', 'lead_status'])

    # Create lead_sources table
    op.create_table(
        'lead_sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False, server_default='apify'),
        sa.Column('provider_id', sa.String(length=255), nullable=True),
        sa.Column('actor_id', sa.String(length=100), nullable=True),
        sa.Column('actor_name', sa.String(length=255), nullable=True),
        sa.Column('run_id', sa.String(length=100), nullable=True),
        sa.Column('dataset_id', sa.String(length=100), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('external_url', sa.String(length=500), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=True),
        sa.Column('import_batch_id', sa.String(length=100), nullable=True),
        sa.Column('scrape_params', sa.JSON(), nullable=True),
        sa.Column('data_quality_score', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['sales_leads.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lead_id')
    )

    # Indexes for lead_sources
    op.create_index('ix_lead_sources_source_type', 'lead_sources', ['source_type'])
    op.create_index('ix_lead_sources_is_deleted', 'lead_sources', ['is_deleted'])
    op.create_index('idx_source_provider', 'lead_sources', ['provider_name', 'external_id'])
    op.create_index('idx_source_actor_run', 'lead_sources', ['actor_id', 'run_id'])
    op.create_index('idx_source_batch', 'lead_sources', ['import_batch_id'])

    # Create apify_sync_states table
    op.create_table(
        'apify_sync_states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('actor_id', sa.String(length=100), nullable=False),
        sa.Column('actor_name', sa.String(length=255), nullable=True),
        sa.Column('run_id', sa.String(length=100), nullable=False),
        sa.Column('dataset_id', sa.String(length=100), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('next_sync_at', sa.DateTime(), nullable=True),
        sa.Column('run_status', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('total_records', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('synced_records', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_records', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('duplicate_records', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('input_params', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('compute_units', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.String(length=20), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id')
    )

    # Indexes for apify_sync_states
    op.create_index('ix_apify_sync_states_actor_id', 'apify_sync_states', ['actor_id'])
    op.create_index('ix_apify_sync_states_is_deleted', 'apify_sync_states', ['is_deleted'])
    op.create_index('idx_sync_actor_status', 'apify_sync_states', ['actor_id', 'sync_status'])
    op.create_index('idx_sync_run', 'apify_sync_states', ['run_id'])
    op.create_index('idx_sync_status_time', 'apify_sync_states', ['sync_status', 'last_sync_at'])

    # Create lead_events table
    op.create_table(
        'lead_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_name', sa.String(length=255), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=True),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('event_source', sa.String(length=100), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=True),
        sa.Column('old_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=True),
        sa.Column('changed_fields', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['sales_leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for lead_events
    op.create_index('ix_lead_events_lead_id', 'lead_events', ['lead_id'])
    op.create_index('ix_lead_events_event_type', 'lead_events', ['event_type'])
    op.create_index('ix_lead_events_event_timestamp', 'lead_events', ['event_timestamp'])
    op.create_index('idx_event_lead_type', 'lead_events', ['lead_id', 'event_type'])
    op.create_index('idx_event_timestamp', 'lead_events', ['event_timestamp'])
    op.create_index('idx_event_type_time', 'lead_events', ['event_type', 'event_timestamp'])


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('lead_events')
    op.drop_table('apify_sync_states')
    op.drop_table('lead_sources')
    op.drop_table('sales_leads')
    op.drop_table('companies')
