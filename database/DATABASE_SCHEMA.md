# Database Schema - Sales Lead Management System

## Entity Relationship Diagram (ERD)

```
┌─────────────────────────────┐
│        COMPANIES            │
├─────────────────────────────┤
│ PK  id (INTEGER)            │
│     name (VARCHAR 255)      │
│ IDX domain (VARCHAR 255)    │
│     company_type (VARCHAR)  │
│ IDX country (VARCHAR 100)   │
│     city (VARCHAR 100)      │
│ IDX industry (VARCHAR 100)  │
│     employee_count (INT)    │
│     ... (other fields)      │
│ AUDIT/SOFT-DELETE COLUMNS   │
└──────────────┬──────────────┘
               │
               │ 1:N
               │
┌──────────────▼──────────────┐       ┌──────────────────────────┐
│       SALES_LEADS           │       │     LEAD_SOURCES         │
├─────────────────────────────┤       ├──────────────────────────┤
│ PK  id (INTEGER)            │   1:1 │ PK  id (INTEGER)         │
│     full_name (VARCHAR 255) │◄──────┤ FK  lead_id (UNIQUE)     │
│ IDX email (VARCHAR 255)     │       │ IDX source_type          │
│ IDX phone (VARCHAR 50)      │       │     source_name          │
│ IDX company_domain          │       │     provider_name        │
│ FK  company_id              │       │ IDX actor_id             │
│     company_name            │       │ IDX run_id               │
│ IDX country (VARCHAR 100)   │       │     external_id          │
│     city (VARCHAR 100)      │       │ IDX import_batch_id      │
│ IDX source (VARCHAR 50)     │       │     scrape_params (JSON) │
│     provider_name           │       │     metadata (JSON)      │
│ IDX external_id             │       │ AUDIT/SOFT-DELETE        │
│ IDX actor_id                │       └──────────────────────────┘
│ IDX run_id                  │
│     enrichment_status       │
│     lead_status             │       ┌──────────────────────────┐
│     raw_data (JSON)         │       │   APIFY_SYNC_STATES      │
│ AUDIT/SOFT-DELETE COLUMNS   │       ├──────────────────────────┤
└──────────────┬──────────────┘       │ PK  id (INTEGER)         │
               │                      │ IDX actor_id             │
               │ 1:N                  │ UNQ run_id               │
               │                      │     dataset_id           │
┌──────────────▼──────────────┐       │ IDX sync_status          │
│       LEAD_EVENTS           │       │     last_sync_at         │
├─────────────────────────────┤       │     run_status           │
│ PK  id (INTEGER)            │       │     total_records        │
│ FK  lead_id                 │       │     synced_records       │
│ IDX event_type              │       │     failed_records       │
│     event_name              │       │     input_params (JSON)  │
│ IDX event_timestamp         │       │     error_message        │
│     event_data (JSON)       │       │     cost_usd             │
│     actor                   │       │ AUDIT/SOFT-DELETE        │
│     changed_fields (JSON)   │       └──────────────────────────┘
│ AUDIT COLUMNS (created_*)   │
└─────────────────────────────┘
```

## Tables

### 1. companies

Stores unique company information.

**Purpose**: Central repository for company data to avoid duplication.

**Columns**:
- `id` (PK): Primary key
- `name`: Company name
- `domain` (IDX): Company domain/website
- `company_type`: Type (PRIVATE, PUBLIC, etc.)
- `country` (IDX): Country location
- `city`: City location
- `industry` (IDX): Industry sector
- `employee_count`: Number of employees
- `employee_size_min/max`: Employee range
- `description`: Company description
- `website`: Company website URL
- `linkedin_url`: LinkedIn profile
- `tags`: Comma-separated or JSON tags
- Audit columns: `created_at`, `updated_at`, `created_by`, `updated_by`
- Soft-delete: `is_deleted`, `deleted_at`, `deleted_by`

**Indexes**:
- `ix_companies_domain` ON (domain)
- `ix_companies_country` ON (country)
- `ix_companies_industry` ON (industry)
- `idx_company_location` ON (country, city)
- `idx_company_industry_country` ON (industry, country)

**Relationships**:
- One-to-Many with `sales_leads`

---

### 2. sales_leads

Main table storing individual lead information.

**Purpose**: Core table for all lead data with source tracking and enrichment status.

**Columns**:
- `id` (PK): Primary key
- `full_name`, `first_name`, `last_name`: Name fields
- `title`: Job title
- `email` (IDX): Primary email
- `email_verified`: Verification status
- `phone` (IDX): Primary phone
- `phone_verified`: Verification status
- `additional_emails` (JSON): Array of additional emails
- `additional_phones` (JSON): Array of additional phones
- `company_id` (FK): Link to companies table
- `company_name`: Denormalized company name
- `company_domain` (IDX): Denormalized domain
- `country` (IDX), `city`, `state`, `postal_code`: Geographic info
- `industry`: Industry sector
- `tags`: Lead tags
- **Source Tracking**:
  - `source` (IDX): Source type (apify, manual, import)
  - `provider_name`: Provider name (apify)
  - `external_id`: Unique ID from source
  - `actor_id`: Apify actor ID
  - `run_id`: Apify run ID
  - `dataset_id`: Apify dataset ID
- **Enrichment**:
  - `enrichment_status`: pending/enriched/failed
  - `enrichment_data` (JSON): Enriched data
- **Lead Management**:
  - `lead_score`: Lead scoring (0-100)
  - `lead_status`: new/contacted/qualified/converted
- `notes`: Additional notes
- `raw_data` (JSON): Original scraped data
- Audit & soft-delete columns

**Indexes**:
- `ix_sales_leads_email` ON (email)
- `ix_sales_leads_phone` ON (phone)
- `ix_sales_leads_company_domain` ON (company_domain)
- `ix_sales_leads_country` ON (country)
- `ix_sales_leads_source` ON (source)
- `idx_provider_external` ON (provider_name, external_id) ⭐
- `idx_lead_source_actor` ON (source, actor_id)
- `idx_lead_location` ON (country, city)
- `idx_lead_status` ON (lead_status, enrichment_status)
- `idx_lead_company` ON (company_id, lead_status)

**Relationships**:
- Many-to-One with `companies`
- One-to-One with `lead_sources`
- One-to-Many with `lead_events`

---

### 3. lead_sources

Tracks the origin of each lead.

**Purpose**: Detailed source attribution for each lead (one per lead).

**Columns**:
- `id` (PK): Primary key
- `lead_id` (FK, UNIQUE): Link to sales_leads
- `source_type` (IDX): apify/manual/import/api
- `source_name`: Descriptive name
- `provider_name`: Provider (apify)
- `provider_id`: Provider's internal ID
- `actor_id`, `actor_name`: Apify actor info
- `run_id`, `dataset_id`: Apify run info
- `external_id`: External unique identifier
- `external_url`: URL to source record
- `scraped_at`: When data was scraped
- `import_batch_id` (IDX): Batch import identifier
- `scrape_params` (JSON): Input parameters used
- `data_quality_score`: Quality metric (0-100)
- `confidence_score`: Confidence metric (0-100)
- `metadata` (JSON): Additional metadata
- Audit & soft-delete columns

**Indexes**:
- `ix_lead_sources_source_type` ON (source_type)
- `idx_source_provider` ON (provider_name, external_id) ⭐
- `idx_source_actor_run` ON (actor_id, run_id)
- `idx_source_batch` ON (import_batch_id)

**Relationships**:
- One-to-One with `sales_leads`

---

### 4. apify_sync_states

Tracks synchronization status for Apify runs.

**Purpose**: Monitor and manage sync operations from Apify platform.

**Columns**:
- `id` (PK): Primary key
- `actor_id` (IDX): Apify actor identifier
- `actor_name`: Actor display name
- `run_id` (UNIQUE): Unique run identifier
- `dataset_id`: Associated dataset
- `sync_status` (IDX): pending/syncing/completed/failed
- `last_sync_at`, `next_sync_at`: Sync timestamps
- `run_status`: READY/RUNNING/SUCCEEDED/FAILED
- `started_at`, `finished_at`: Run timestamps
- **Metrics**:
  - `total_records`: Total records in run
  - `synced_records`: Successfully synced
  - `failed_records`: Failed to sync
  - `duplicate_records`: Duplicates found
- `input_params` (JSON): Run input parameters
- `error_message`, `error_details` (JSON): Error tracking
- `retry_count`: Number of retry attempts
- `compute_units`: Apify compute units used
- `cost_usd`: Cost in USD
- `metadata` (JSON): Additional metadata
- Audit & soft-delete columns

**Indexes**:
- `ix_apify_sync_states_actor_id` ON (actor_id)
- `idx_sync_actor_status` ON (actor_id, sync_status)
- `idx_sync_run` ON (run_id)
- `idx_sync_status_time` ON (sync_status, last_sync_at)

**Relationships**:
- No direct foreign key relationships (tracking table)

---

### 5. lead_events

Event log for lead activities and changes.

**Purpose**: Audit trail of all lead-related activities.

**Columns**:
- `id` (PK): Primary key
- `lead_id` (FK, IDX): Link to sales_leads
- `event_type` (IDX): created/updated/contacted/enriched/deleted
- `event_name`: Event display name
- `event_description`: Detailed description
- `event_data` (JSON): Flexible event data
- `event_source`: Where event originated
- `event_timestamp` (IDX): When event occurred
- `actor`: User/system who triggered event
- `old_status`, `new_status`: Status changes
- `changed_fields` (JSON): Field-level changes
- Audit columns (created_at, updated_at)

**Indexes**:
- `ix_lead_events_lead_id` ON (lead_id)
- `ix_lead_events_event_type` ON (event_type)
- `ix_lead_events_event_timestamp` ON (event_timestamp)
- `idx_event_lead_type` ON (lead_id, event_type)
- `idx_event_type_time` ON (event_type, event_timestamp)

**Relationships**:
- Many-to-One with `sales_leads`

---

## Key Design Patterns

### 1. Audit Columns (All Tables)
Every table includes:
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp
- `created_by`: User/system who created
- `updated_by`: User/system who last updated

### 2. Soft Delete (All Tables except lead_events)
Enables data recovery:
- `is_deleted` (BOOL, indexed): Soft delete flag
- `deleted_at`: When deleted
- `deleted_by`: Who deleted

### 3. Source Attribution
Multi-level tracking:
- **sales_leads**: Basic source info (source, provider_name, external_id, actor_id, run_id)
- **lead_sources**: Detailed source metadata
- **apify_sync_states**: Sync operation tracking

### 4. Denormalization
Strategic denormalization for performance:
- `company_name`, `company_domain` in `sales_leads`
- Allows queries without JOIN

### 5. JSON Columns
Flexible data storage:
- `additional_emails`, `additional_phones`: Arrays
- `raw_data`, `enrichment_data`: Complex objects
- `scrape_params`, `event_data`: Flexible metadata

## Critical Indexes

### Composite Indexes (Performance)
1. `idx_provider_external` ON (provider_name, external_id)
   - Fast deduplication checks
   - Prevents duplicate imports

2. `idx_lead_source_actor` ON (source, actor_id)
   - Query leads by source and actor

3. `idx_lead_location` ON (country, city)
   - Geographic queries

4. `idx_company_industry_country` ON (industry, country)
   - Industry + location filtering

### Single Column Indexes
- All foreign keys
- `email`, `phone` for lookups
- `is_deleted` for filtering active records
- `event_timestamp` for chronological queries

## Usage Patterns

### 1. Import from Apify
```sql
-- Check if already synced
SELECT * FROM apify_sync_states WHERE run_id = ?

-- Create sync state
INSERT INTO apify_sync_states (actor_id, run_id, ...)

-- Check for duplicates
SELECT * FROM sales_leads
WHERE provider_name = 'apify' AND external_id = ?

-- Insert lead
INSERT INTO sales_leads (...)
INSERT INTO lead_sources (...)
INSERT INTO lead_events (event_type = 'created', ...)

-- Update sync state
UPDATE apify_sync_states SET sync_status = 'completed', ...
```

### 2. Query Active Leads
```sql
SELECT * FROM sales_leads
WHERE is_deleted = FALSE
  AND country = 'India'
  AND lead_status = 'new'
ORDER BY created_at DESC
LIMIT 100
```

### 3. Get Lead History
```sql
SELECT * FROM lead_events
WHERE lead_id = ?
ORDER BY event_timestamp DESC
```

## Migration Strategy

### Initial Migration (001_initial)
- Creates all 5 tables
- Creates all indexes
- Sets up foreign key constraints

### Rollback
```bash
# Downgrade to base
alembic downgrade base

# Or specific revision
alembic downgrade -1
```

## Database Support

- **SQLite**: Default (development)
- **PostgreSQL**: Production recommended (JSON support, performance)
- **MySQL**: Supported (requires JSON datatype support)

## Size Estimates

For 100,000 leads:
- `companies`: ~5,000 rows (~2 MB)
- `sales_leads`: 100,000 rows (~50 MB)
- `lead_sources`: 100,000 rows (~30 MB)
- `lead_events`: 500,000 rows (~100 MB)
- `apify_sync_states`: ~1,000 rows (~1 MB)

**Total**: ~183 MB for 100K leads

## Maintenance

### Cleanup Soft-Deleted Records
```sql
-- Find old deleted records (>90 days)
SELECT COUNT(*) FROM sales_leads
WHERE is_deleted = TRUE
  AND deleted_at < NOW() - INTERVAL '90 days'

-- Hard delete (use with caution)
DELETE FROM sales_leads
WHERE is_deleted = TRUE
  AND deleted_at < NOW() - INTERVAL '90 days'
```

### Index Maintenance
```sql
-- PostgreSQL: Rebuild indexes
REINDEX TABLE sales_leads;

-- Check index usage
SELECT * FROM pg_stat_user_indexes;
```

## Acceptance Criteria ✓

- [x] Tables: sales_leads, companies, lead_sources, apify_sync_state, lead_events
- [x] Source tracking columns (source, provider_name, external_id, actor_id, run_id)
- [x] Contact fields (emails, phones)
- [x] Geographic columns (country, city)
- [x] Industry and tags
- [x] Enrichment status tracking
- [x] Timestamps (created_at, updated_at)
- [x] Indexes on (provider, external_id), (email), (company_domain), (country)
- [x] Soft-delete columns
- [x] Audit columns
- [x] Migration scripts with upgrade/downgrade
- [x] CRUD operations via ORM
