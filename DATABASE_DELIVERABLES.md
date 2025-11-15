# Database Implementation - Deliverables

## ✅ Acceptance Criteria Met

### Tables Created
- [x] **sales_leads** - Main leads table with all tracking fields
- [x] **companies** - Company information
- [x] **lead_sources** - Source attribution
- [x] **apify_sync_state** - Sync tracking
- [x] **lead_events** - Activity audit trail

### Required Columns Implemented
- [x] `source` - Source type (apify, manual, import)
- [x] `provider_name` - Provider identifier (apify)
- [x] `external_id` - Unique ID from source system
- [x] `actor_id` - Apify actor identifier
- [x] `run_id` - Apify run identifier
- [x] `email` / `phone` - Contact information (indexed)
- [x] `country` / `city` - Geographic data (indexed)
- [x] `industry` - Industry classification
- [x] `tags` - Flexible tagging system
- [x] `enrichment_status` - Enrichment tracking
- [x] Timestamps - `created_at`, `updated_at`

### Indexes Created
- [x] `(provider_name, external_id)` - Deduplication
- [x] `(email)` - Email lookup
- [x] `(company_domain)` - Domain lookup
- [x] `(country)` - Geographic filtering
- [x] Additional composite indexes for performance

### Audit & Soft Delete
- [x] **Audit columns** on all tables:
  - `created_at`, `updated_at`
  - `created_by`, `updated_by`
- [x] **Soft-delete columns**:
  - `is_deleted` (indexed)
  - `deleted_at`
  - `deleted_by`

### Migration Scripts
- [x] **Initial migration** (`20251114_initial_schema.py`)
  - Creates all 5 tables
  - Creates all indexes and constraints
  - Full rollback support
- [x] **Alembic configuration** (alembic.ini, env.py)
- [x] **Migration management** via Alembic CLI

### ERD Documentation
- [x] **DATABASE_SCHEMA.md** - Complete ERD with:
  - Visual entity relationship diagram
  - Full table specifications
  - Index definitions
  - Usage patterns
  - Maintenance guidelines

### CRUD Operations
- [x] **LeadCRUD** - Full CRUD for sales_leads
  - create, get_by_id, get_by_email, get_by_external_id
  - list_leads, update, delete (soft), restore, count
- [x] **CompanyCRUD** - Company management
  - create, get_by_id, get_by_domain, get_or_create, update
- [x] **LeadSourceCRUD** - Source tracking
- [x] **ApifySyncCRUD** - Sync state management
- [x] **EventCRUD** - Event logging

## 📁 Files Delivered

### Core Database Files
```
database/
├── __init__.py                     # Package init
├── config.py                       # Database configuration
├── session.py                      # Session management
├── crud.py                         # CRUD operations
├── README.md                       # Usage documentation
├── DATABASE_SCHEMA.md              # ERD and schema specs
│
├── models/                         # ORM Models
│   ├── __init__.py
│   ├── base.py                     # Base model with audit/soft-delete
│   ├── companies.py                # Company model
│   ├── sales_leads.py              # SalesLead model
│   ├── lead_sources.py             # LeadSource model
│   ├── apify_sync_state.py         # ApifySyncState model
│   └── lead_events.py              # LeadEvent model
│
└── migrations/                     # Alembic migrations
    ├── env.py                      # Migration environment
    ├── script.py.mako              # Migration template
    └── versions/
        └── 20251114_initial_schema.py  # Initial migration
```

### Configuration Files
```
alembic.ini                         # Alembic configuration
.env.example                        # Environment template (updated)
requirements.txt                    # Dependencies (updated)
```

### Management Scripts
```
scripts/
└── db_manage.py                    # Database management CLI
    Commands:
    - init      # Initialize database
    - drop      # Drop all tables
    - test      # Test CRUD operations
    - schema    # Show database schema
    - reset     # Drop and recreate
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
# Method 1: Using management script
python scripts/db_manage.py init

# Method 2: Using Alembic
alembic upgrade head
```

### 3. Test CRUD
```bash
python scripts/db_manage.py test
```

Expected output:
```
✓ Company created: ID=1, Name=Test Company Inc
✓ Lead created: ID=1, Name=John Doe, Email=john.doe@testcompany.com
✓ Lead source created: ID=1
✓ Sync state created: ID=1, Run ID=test_run_123
✓ Get by ID: John Doe
✓ Get by email: John Doe
✓ Lead updated: Status=contacted
✓ Lead has 3 events
✓ Lead soft deleted: is_deleted=True
✓ Lead restored: is_deleted=False
✓ Listed 1 leads
✓ Total leads: 1
✓ All CRUD tests passed successfully!
```

## 📊 Database Schema Summary

### Tables & Relationships

```
companies (1) ──┬──> (N) sales_leads
                │
sales_leads (1) ├──> (1) lead_sources
                │
                └──> (N) lead_events

apify_sync_states (independent tracking table)
```

### Key Indexes

**Deduplication:**
- `(provider_name, external_id)` on sales_leads
- `(provider_name, external_id)` on lead_sources

**Lookups:**
- `email`, `phone` on sales_leads
- `company_domain` on sales_leads
- `domain` on companies

**Filtering:**
- `country` on sales_leads and companies
- `industry` on sales_leads and companies
- `(country, city)` composite on both

**Status:**
- `(lead_status, enrichment_status)` on sales_leads
- `(sync_status, last_sync_at)` on apify_sync_states

## 💻 ORM Shell Examples

### Create Lead
```python
from database.session import session_scope
from database.crud import LeadCRUD

with session_scope() as session:
    lead = LeadCRUD.create(
        session=session,
        full_name="Jane Smith",
        email="jane@company.com",
        source="apify",
        provider_name="apify",
        external_id="ext_123",
        actor_id="T1XDXWc1L92AfIJtd",
        run_id="run_456",
        country="India",
        city="Chennai"
    )
    print(f"Created lead ID: {lead.id}")
```

### Query Leads
```python
from database.session import get_session
from database.crud import LeadCRUD

session = get_session()

# Get by email
lead = LeadCRUD.get_by_email(session, "jane@company.com")

# List with filters
leads = LeadCRUD.list_leads(
    session,
    filters={'country': 'India', 'source': 'apify'},
    limit=100
)

# Count
total = LeadCRUD.count(session, filters={'country': 'India'})

session.close()
```

### Update Lead
```python
with session_scope() as session:
    lead = LeadCRUD.update(
        session,
        lead_id=1,
        lead_status="contacted",
        enrichment_status="enriched",
        updated_by="system"
    )
```

### Track Events
```python
from database.crud import EventCRUD

with session_scope() as session:
    # Events are auto-created for create/update/delete
    # Get history
    events = EventCRUD.get_lead_events(session, lead_id=1)
    for event in events:
        print(f"{event.event_type}: {event.event_name}")
```

## 🧪 Testing

### Run All Tests
```bash
python scripts/db_manage.py test
```

### Manual Testing
```python
# Start Python shell
python

# Import and test
from database.session import session_scope
from database.crud import LeadCRUD

with session_scope() as session:
    # Create
    lead = LeadCRUD.create(
        session=session,
        email="test@example.com",
        source="apify"
    )

    # Read
    found = LeadCRUD.get_by_email(session, "test@example.com")
    print(f"Found: {found.email}")

    # Update
    updated = LeadCRUD.update(session, found.id, lead_status="contacted")
    print(f"Status: {updated.lead_status}")

    # Delete
    LeadCRUD.delete(session, found.id)
    print("Deleted")
```

## 📝 Migration Commands

```bash
# Run migrations
alembic upgrade head

# Check current version
alembic current

# View history
alembic history --verbose

# Rollback one step
alembic downgrade -1

# Rollback to base
alembic downgrade base

# Create new migration (after model changes)
alembic revision --autogenerate -m "description"
```

## 🔧 Configuration Options

### SQLite (Default)
```bash
# In .env or environment
DATABASE_URL=sqlite:///data/sales_leads.db
```

### PostgreSQL
```bash
pip install psycopg2-binary
DATABASE_URL=postgresql://user:pass@localhost/sales_leads
```

### MySQL
```bash
pip install pymysql
DATABASE_URL=mysql+pymysql://user:pass@localhost/sales_leads
```

## ✅ Verification Checklist

- [x] Migrations run clean locally
- [x] All 5 tables created
- [x] All required columns present
- [x] Indexes created correctly
- [x] Soft-delete functionality works
- [x] Audit columns populated
- [x] CRUD operations work via ORM
- [x] Foreign key constraints enforced
- [x] Rollback migrations work
- [x] ERD documentation complete
- [x] No dependencies on external services

## 📚 Documentation

1. **database/README.md** - Usage guide and API reference
2. **database/DATABASE_SCHEMA.md** - Complete ERD and specifications
3. **This file** - Deliverables summary

## 🎯 Next Steps

### Integration with Scrapers
```python
# Example: Store scraped data
from src.email_scraper import EmailScraper
from database.session import session_scope
from database.crud import LeadCRUD, ApifySyncCRUD

scraper = EmailScraper()
run_data, results = scraper.scrape(
    organization_locations=["chennai"],
    max_results=100
)

with session_scope() as session:
    # Track sync
    sync = ApifySyncCRUD.create(
        session=session,
        actor_id=run_data['actId'],
        run_id=run_data['id'],
        total_records=len(results)
    )

    # Store leads
    for item in results:
        lead = LeadCRUD.create(
            session=session,
            email=item.get('email'),
            source='apify',
            actor_id=run_data['actId'],
            run_id=run_data['id'],
            raw_data=item
        )

    sync.mark_completed(synced_count=len(results))
```

## 🎉 Summary

✅ **Complete database implementation delivered**

- 5 tables with full relationships
- All required columns and indexes
- Audit and soft-delete on all tables
- Migration scripts with rollback
- CRUD operations via ORM
- Comprehensive documentation with ERD
- Management scripts for easy operation
- Tested and verified locally

**Status**: READY FOR USE
