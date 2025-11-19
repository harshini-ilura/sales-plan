# Guide: Scraping Leads with Apify and Viewing in Web UI

This guide explains how to scrape leads using Apify actors and view them in the web UI at `http://localhost:8080/leads`.

## Quick Start

### 1. Scrape Leads and Save to Database

Use the scraping script with the `--save-to-db` flag to automatically import leads into the database:

```bash
# Scrape emails from Chennai and save to database
python scripts/scrape_leads_apify.py --type email --locations chennai --save-to-db

# Scrape phone numbers from Dubai and save to database
python scripts/scrape_leads_apify.py --type phone --locations dubai --save-to-db

# Scrape both emails and phones with filters
python scripts/scrape_leads_apify.py --type both \
  --locations chennai dubai \
  --industries software technology \
  --max-results 200 \
  --save-to-db
```

### 2. View Leads in Web UI

1. Start the web server:
   ```bash
   python web_ui/app.py
   ```

2. Open your browser to:
   ```
   http://localhost:8080/leads
   ```

3. You'll see all imported leads with:
   - Company name
   - Contact name
   - Email
   - Phone
   - Location
   - Industry
   - Source

## Detailed Usage

### Scraping Options

#### Basic Email Scraping
```bash
python scripts/scrape_leads_apify.py --type email \
  --locations chennai \
  --save-to-db
```

#### Phone Number Scraping
```bash
python scripts/scrape_leads_apify.py --type phone \
  --locations dubai \
  --save-to-db
```

#### Both Emails and Phones
```bash
python scripts/scrape_leads_apify.py --type both \
  --locations chennai dubai \
  --save-to-db
```

#### With Industry Filter
```bash
python scripts/scrape_leads_apify.py --type email \
  --locations chennai \
  --industries software technology "IT Services" \
  --save-to-db
```

#### With Company Size Filter
```bash
python scripts/scrape_leads_apify.py --type phone \
  --locations dubai \
  --employee-min 50 \
  --employee-max 500 \
  --save-to-db
```

#### Limit Results
```bash
python scripts/scrape_leads_apify.py --type email \
  --locations chennai \
  --max-results 50 \
  --save-to-db
```

### Import from Existing Files

If you have previously scraped data saved as JSON files, you can import them:

```bash
python scripts/import_apify_leads.py \
  --file data/exports/email_leads_chennai_20251114_123043.json \
  --actor-id T1XDXWc1L92AfIJtd \
  --actor-name "Apify Email Scraper"
```

### What Gets Saved

When you use `--save-to-db`, the script will:

1. **Scrape leads** using Apify actors
2. **Save to files** (JSON/CSV) as before
3. **Import to database** with:
   - Lead information (name, email, phone, company, location)
   - Source tracking (which Apify actor, run ID, etc.)
   - Company records (deduplicated by domain)
   - Lead source metadata

### Database Tables Used

- **sales_leads**: Main lead records
- **companies**: Company information (deduplicated)
- **lead_sources**: Source tracking for each lead
- **apify_sync_states**: Sync operation tracking

### Deduplication

The import process automatically:
- **Skips duplicates** by email address
- **Skips duplicates** by external ID (Apify record ID)
- **Merges company data** by domain name

### Viewing Leads in Web UI

After importing, visit `http://localhost:8080/leads` to see:

- All imported leads in a paginated table
- Filterable by source, country, industry
- Searchable by company name, email, etc.

## Troubleshooting

### No Leads Showing in Web UI

1. **Check if database was initialized:**
   ```bash
   python scripts/db_manage.py init
   ```

2. **Verify leads were imported:**
   ```bash
   python -c "
   from database.session import get_session
   from database.models import SalesLead
   session = get_session()
   count = session.query(SalesLead).count()
   print(f'Total leads in database: {count}')
   session.close()
   "
   ```

3. **Check import logs** - the script will show:
   - Total records processed
   - How many were imported
   - How many were skipped (duplicates)
   - Any errors

### Import Errors

- **Check database connection** - ensure database file exists
- **Check Apify API token** - must be set in `.env` file
- **Check data format** - ensure Apify results are valid

### Duplicate Leads

The system automatically skips duplicates. If you want to re-import:
- Delete existing leads first, or
- The system will skip duplicates automatically

## Example Workflow

```bash
# 1. Scrape emails from Chennai (tech companies)
python scripts/scrape_leads_apify.py \
  --type email \
  --locations chennai \
  --industries software technology \
  --max-results 100 \
  --save-to-db

# 2. Start web UI
python web_ui/app.py

# 3. Open browser to http://localhost:8080/leads

# 4. View and use leads for email campaigns!
```

## Next Steps

After importing leads:

1. **Create Email Templates** (`/templates/create`)
2. **Create Campaigns** (`/campaigns/create`)
3. **Queue Emails** for bulk sending
4. **Track Results** in campaign dashboard

See `WEB_UI_GUIDE.md` for more details on using the email campaign features.

