# Sales Lead Database

Complete database implementation for storing and managing sales leads from Apify scrapers.

## Quick Start

### 1. Install Dependencies

```bash
pip install sqlalchemy alembic
```

### 2. Initialize Database

```bash
# Using management script
python scripts/db_manage.py init

# Or using Alembic
alembic upgrade head
```

### 3. Test CRUD Operations

```bash
python scripts/db_manage.py test
```

## Database Structure

5 tables with full audit and soft-delete support:

1. **companies** - Company information
2. **sales_leads** - Lead data with source tracking
3. **lead_sources** - Detailed source attribution
4. **apify_sync_states** - Sync operation tracking
5. **lead_events** - Activity audit trail

See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for complete ERD and specifications.

## Usage

### Using Session Context Manager

```python
from database.session import session_scope
from database.crud import LeadCRUD

with session_scope() as session:
    lead = LeadCRUD.create(
        session=session,
        full_name="John Doe",
        email="john@example.com",
        source="apify",
        provider_name="apify",
        actor_id="T1XDXWc1L92AfIJtd"
    )
    # Automatically committed
```

### Manual Session Management

```python
from database.session import get_session
from database.crud import LeadCRUD

session = get_session()
try:
    lead = LeadCRUD.create(session, **data)
    session.commit()
except Exception as e:
    session.rollback()
    raise
finally:
    session.close()
```

## CRUD Operations

### Create Lead

```python
from database.session import session_scope
from database.crud import LeadCRUD, CompanyCRUD

with session_scope() as session:
    # Create company
    company = CompanyCRUD.create(
        session=session,
        name="Acme Corp",
        domain="acme.com",
        country="USA",
        industry="technology"
    )

    # Create lead
    lead = LeadCRUD.create(
        session=session,
        full_name="Jane Smith",
        email="jane@acme.com",
        phone="+1-555-1234",
        company_id=company.id,
        country="USA",
        source="apify",
        actor_id="T1XDXWc1L92AfIJtd",
        run_id="run_12345"
    )
```

### Read Leads

```python
# Get by ID
lead = LeadCRUD.get_by_id(session, lead_id=1)

# Get by email
lead = LeadCRUD.get_by_email(session, email="jane@acme.com")

# Get by external ID
lead = LeadCRUD.get_by_external_id(
    session,
    provider="apify",
    external_id="ext_123"
)

# List with filters
leads = LeadCRUD.list_leads(
    session,
    filters={
        'country': 'USA',
        'source': 'apify',
        'lead_status': 'new'
    },
    limit=100
)

# Count
count = LeadCRUD.count(session, filters={'country': 'India'})
```

### Update Lead

```python
lead = LeadCRUD.update(
    session,
    lead_id=1,
    lead_status="contacted",
    enrichment_status="enriched",
    updated_by="system"
)
```

### Delete (Soft Delete)

```python
# Soft delete
LeadCRUD.delete(session, lead_id=1, deleted_by="admin")

# Restore
lead = LeadCRUD.restore(session, lead_id=1)
```

### Events

```python
from database.crud import EventCRUD

# Create custom event
EventCRUD.create_event(
    session=session,
    lead_id=1,
    event_type="contacted",
    event_name="Email Sent",
    event_description="Initial outreach email sent",
    actor="sales_rep"
)

# Get lead history
events = EventCRUD.get_lead_events(session, lead_id=1, limit=50)
```

## Migrations

### Run Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Check current version
alembic current

# View history
alembic history
```

### Rollback

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to base (empty database)
alembic downgrade base
```

### Create New Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "description"

# Empty migration template
alembic revision -m "description"
```

## Management Commands

```bash
# Initialize database
python scripts/db_manage.py init

# Drop all tables (caution!)
python scripts/db_manage.py drop

# Test CRUD operations
python scripts/db_manage.py test

# Show schema
python scripts/db_manage.py schema

# Reset database (drop + init)
python scripts/db_manage.py reset
```

## Configuration

### SQLite (Default)

```python
# .env or environment
DATABASE_URL=sqlite:///data/sales_leads.db
```

### PostgreSQL

```python
# Install driver
pip install psycopg2-binary

# Set URL
DATABASE_URL=postgresql://user:password@localhost/sales_leads
```

### MySQL

```python
# Install driver
pip install pymysql

# Set URL
DATABASE_URL=mysql+pymysql://user:password@localhost/sales_leads
```

## Features

### Audit Trail
All tables track:
- `created_at`, `updated_at`
- `created_by`, `updated_by`

### Soft Delete
All tables support soft delete:
- `is_deleted` flag
- `deleted_at` timestamp
- `deleted_by` user

Query excludes soft-deleted by default:
```python
# Excludes deleted
lead = LeadCRUD.get_by_id(session, 1)

# Include deleted
lead = LeadCRUD.get_by_id(session, 1, include_deleted=True)
```

### Source Tracking
Complete lineage for each lead:
- Source type (apify, manual, import)
- Provider details
- Actor and run IDs
- Original scrape parameters

### Event Logging
Automatic events for:
- Lead created
- Lead updated (with field changes)
- Lead deleted

Custom events supported.

## Performance

### Indexes
- All foreign keys indexed
- Composite indexes for common queries
- See DATABASE_SCHEMA.md for complete list

### Query Optimization
```python
# Use filters dictionary for indexed queries
leads = LeadCRUD.list_leads(
    session,
    filters={'country': 'India'},  # Uses index
    limit=100
)

# Pagination
leads = LeadCRUD.list_leads(session, skip=100, limit=100)
```

## Integration with Scrapers

### Store Scraped Data

```python
from src.email_scraper import EmailScraper
from database.session import session_scope
from database.crud import LeadCRUD, ApifySyncCRUD

# Run scraper
scraper = EmailScraper()
run_data, results = scraper.scrape(
    organization_locations=["chennai"],
    max_results=100
)

# Store in database
with session_scope() as session:
    # Track sync
    sync_state = ApifySyncCRUD.create(
        session=session,
        actor_id=run_data['actId'],
        run_id=run_data['id'],
        dataset_id=run_data['defaultDatasetId'],
        total_records=len(results),
        sync_status='syncing'
    )

    synced = 0
    for item in results:
        # Check for duplicate
        existing = LeadCRUD.get_by_external_id(
            session,
            provider="apify",
            external_id=item.get('id')
        )

        if not existing:
            lead = LeadCRUD.create(
                session=session,
                full_name=item.get('fullName'),
                email=item.get('email'),
                source='apify',
                provider_name='apify',
                external_id=item.get('id'),
                actor_id=run_data['actId'],
                run_id=run_data['id'],
                raw_data=item
            )
            synced += 1

    # Update sync status
    sync_state.mark_completed(synced_count=synced)
```

## Testing

Run all tests:

```bash
python scripts/db_manage.py test
```

Expected output:
- ✓ Company created
- ✓ Lead created
- ✓ Lead source created
- ✓ Sync state created
- ✓ CRUD operations work
- ✓ Events logged
- ✓ Soft delete works
- ✓ Restore works

## Troubleshooting

### Migration Issues

```bash
# Check current version
alembic current

# View migration history
alembic history

# Stamp database at specific version
alembic stamp head
```

### Connection Issues

```python
# Test connection
from database.session import engine
engine.connect()
```

### Clear Database

```bash
# Remove SQLite file
rm data/sales_leads.db

# Reinitialize
python scripts/db_manage.py init
```

## Schema Documentation

Complete schema with ERD: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)

Includes:
- Entity relationship diagram
- Table specifications
- Index definitions
- Usage patterns
- Size estimates
