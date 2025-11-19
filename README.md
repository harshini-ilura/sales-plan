# Sales Plan - Lead Management & Email Campaign System

A comprehensive Python application for scraping leads, managing contacts, and sending bulk email campaigns with a modern web interface.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API token
# APIFY_API_TOKEN=your_token_here
```

### 3. Initialize Database

```bash
python scripts/db_manage.py init
```

### 4. Start the Web UI

```bash
python web_ui/app.py
```

The web interface will be available at: **http://localhost:8080**

### 5. Import Leads

You can import leads in two ways:

**Option A: Scrape from Apify**
```bash
python scripts/scrape_leads_apify.py --type email --locations chennai --save-to-db
```

**Option B: Import from CSV**
1. Go to http://localhost:8080/leads/import
2. Upload your CSV file
3. Leads will be imported automatically

## Features

### Lead Management
- **Dual Actor Integration**: Combines email and phone number scrapers from Apify
- **CSV Import**: Import leads from any CSV file (Apollo, LinkedIn, etc.)
- **Smart Filtering**: Filter by location, industry, company size, and type
- **Automatic Polling**: Waits for actor completion and retrieves results
- **Multiple Formats**: Export to JSON, CSV, or both
- **Data Management**: Built-in deduplication and merging

### Email Campaigns
- **Web-Based UI**: Modern, user-friendly interface for managing campaigns
- **Template System**: Create reusable email templates with variables
- **Bulk Sending**: Send emails to hundreds of leads at once
- **Campaign Tracking**: Monitor sent, delivered, opened, and clicked emails
- **Follow-up Automation**: Schedule automatic follow-up emails
- **Multiple Providers**: Support for SMTP, SendGrid, and AWS SES
- **File Attachments**: Attach files and images to your emails

### Production Ready
- Error handling, logging, and retry logic
- Database-backed with SQLAlchemy ORM
- Rate limiting and email queue management

## Integrated Actors

### Email Scraper
- **Actor ID**: `T1XDXWc1L92AfIJtd`
- **Purpose**: Extract verified email addresses
- **URL**: https://console.apify.com/actors/T1XDXWc1L92AfIJtd

### Phone Scraper
- **Actor ID**: `aihL2lJmGDt9XFCGg`
- **Purpose**: Extract phone numbers and company data
- **URL**: https://console.apify.com/actors/aihL2lJmGDt9XFCGg

## Usage Examples

### CLI Usage

```bash
# Scrape emails from Chennai
python scripts/scrape_leads_apify.py --type email --locations chennai

# Scrape phone numbers from Dubai with industry filter
python scripts/scrape_leads_apify.py --type phone \
  --locations dubai \
  --industries software technology

# Scrape both emails and phones with advanced filters
python scripts/scrape_leads_apify.py --type both \
  --locations chennai dubai \
  --industries software \
  --employee-min 10 \
  --employee-max 500 \
  --max-results 200
```

### Programmatic Usage

```python
from src.email_scraper import EmailScraper
from src.phone_scraper import PhoneScraper
from src.data_manager import DataManager

# Email scraping
scraper = EmailScraper()
run_data, results = scraper.scrape(
    organization_locations=["chennai"],
    max_results=100
)

# Phone scraping
phone_scraper = PhoneScraper()
run_data, results = phone_scraper.scrape(
    organization_locations=["dubai"],
    industries=["software"],
    max_results=100
)

# Save results
dm = DataManager()
dm.save_both_formats(results, filename="leads")
```

## Project Structure

```
sales-plan/
├── web_ui/                   # Web interface (Flask)
│   ├── app.py               # Main Flask application
│   └── templates/           # HTML templates
│       ├── base.html
│       ├── dashboard.html
│       ├── campaigns.html
│       ├── templates.html
│       └── leads.html
├── database/                 # Database models and migrations
│   ├── models/              # SQLAlchemy models
│   ├── migrations/          # Alembic migrations
│   └── crud.py             # CRUD operations
├── email_service/           # Email campaign logic
│   ├── campaign_manager.py  # Campaign management
│   ├── queue_processor.py   # Email queue processor
│   └── providers.py         # Email providers (SMTP, SendGrid, SES)
├── config/
│   └── config.yaml          # Configuration
├── src/
│   ├── apify_client.py      # Core API client
│   ├── email_scraper.py     # Email scraper
│   ├── phone_scraper.py     # Phone scraper
│   └── data_manager.py      # Data management
├── scripts/
│   ├── scrape_leads_apify.py # CLI scraping interface
│   ├── import_apify_leads.py # Import Apify results
│   ├── import_csv_leads.py   # Import CSV files
│   └── email_campaign.py    # Campaign CLI
├── data/
│   ├── exports/             # Scraped data exports
│   └── uploads/              # Uploaded files (CSV, attachments)
└── requirements.txt         # Python dependencies
```

## Web UI (Frontend) - Quick Guide

### Starting the Web Server

```bash
# Start the Flask web server
python web_ui/app.py
```

The server will start on **http://localhost:8080** (default port 8080 to avoid macOS AirPlay conflicts).

**Custom Port:**
```bash
PORT=5000 python web_ui/app.py
```

### Accessing the Web Interface

Once the server is running, open your browser and navigate to:

- **Dashboard**: http://localhost:8080/
- **Campaigns**: http://localhost:8080/campaigns
- **Templates**: http://localhost:8080/templates
- **Leads**: http://localhost:8080/leads
- **Import Leads**: http://localhost:8080/leads/import

### Web UI Features

#### 1. Dashboard (`/`)
- Overview of all campaigns, leads, and email statistics
- Quick access to create campaigns, templates, and import leads

#### 2. Lead Management (`/leads`)
- View all imported leads in a paginated table
- Filter by source, country, industry
- Import leads from CSV files
- See lead details: name, email, phone, company, location

#### 3. Email Templates (`/templates`)
- Create and edit email templates
- Use variables: `{{first_name}}`, `{{company_name}}`, etc.
- Support for plain text and HTML
- Template types: Initial, Follow-up, Custom

#### 4. Campaigns (`/campaigns`)
- Create email campaigns with targeting filters
- Configure email provider (SMTP, SendGrid, AWS SES)
- Set up SMTP credentials
- Upload attachments (files, images)
- Queue emails for sending
- Send emails directly from the web UI
- Track campaign statistics

### Complete Workflow

1. **Import Leads**
   - Go to `/leads/import`
   - Upload CSV file or scrape from Apify
   - Leads appear in `/leads`

2. **Create Template**
   - Go to `/templates/create`
   - Design your email template
   - Use variables for personalization

3. **Create Campaign**
   - Go to `/campaigns/create`
   - Select template, configure sender, set filters
   - Add SMTP credentials and attachments

4. **Queue & Send**
   - Go to campaign detail page
   - Click "Queue Emails" to add to queue
   - Click "Send Pending Emails" to send immediately

### Web UI Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- No additional frontend build step required (uses Bootstrap CDN)

## Documentation

See additional guides:
- **[WEB_UI_GUIDE.md](WEB_UI_GUIDE.md)** - Complete web UI usage guide
- **[HOW_TO_SEND_EMAILS.md](HOW_TO_SEND_EMAILS.md)** - Email sending workflow
- **[SCRAPE_AND_IMPORT_GUIDE.md](SCRAPE_AND_IMPORT_GUIDE.md)** - Lead scraping and import
- **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - Detailed setup and CLI reference

## Requirements

- **Python 3.7+** (Python 3.11+ recommended)
- **Apify API token** (for scraping leads)
- **Database**: SQLite (default) or PostgreSQL/MySQL
- **Dependencies**: See `requirements.txt`
  - Flask (web framework)
  - SQLAlchemy (ORM)
  - Flask-WTF (forms)
  - Werkzeug (file uploads)
  - Requests (API client)
  - Python-dotenv (environment variables)

## Configuration

### Environment Variables

```bash
APIFY_API_TOKEN=your_token_here
```

### Actor Configuration

Edit `config/config.yaml` to customize default parameters, timeouts, and export settings.

## Output

Results are saved to `data/exports/` in your chosen format:

```json
[
  {
    "email": "contact@company.com",
    "phone": "+971-xxx-xxxxx",
    "companyName": "Tech Company",
    "location": "Dubai",
    "industry": "Software"
  }
]
```

## API Workflow

1. **Start Run**: Submit actor run with parameters
2. **Poll Status**: Check run status every 5 seconds
3. **Retrieve Results**: Fetch dataset items when complete
4. **Export**: Save to JSON/CSV

## Cost

Pricing: ~$0.002 USD per result (from actor pricing)

Monitor usage: https://console.apify.com/billing

## Error Handling

The implementation includes:
- Automatic retries for failed requests
- Timeout handling for long-running actors
- Detailed logging for debugging
- Graceful error messages

## Best Practices

1. Start with small result sets (10-50)
2. Use specific filters to target relevant leads
3. Monitor API costs in Apify console
4. Save results incrementally for large datasets
5. Use `--type both` for automatic deduplication

## Troubleshooting

### Web UI Issues

**Port Already in Use?**
```bash
# Use a different port
PORT=5000 python web_ui/app.py
```

**Database Not Initialized?**
```bash
python scripts/db_manage.py init
```

**No Leads Showing?**
- Import leads via CSV: http://localhost:8080/leads/import
- Or scrape from Apify: `python scripts/scrape_leads_apify.py --type email --locations chennai --save-to-db`

**Emails Not Sending?**
- Check SMTP credentials in campaign settings
- For Gmail: Use App Password (not regular password)
- Click "Send Pending Emails" button on campaign page
- Or run queue processor: `python -m email_service.queue_processor --once`

### Scraping Issues

**Token not found?**
```bash
# Set in .env file
echo "APIFY_API_TOKEN=your_token" > .env
```

**No results?**
- Check location/industry spelling
- Try broader filters
- Verify actor has data for your criteria

**Timeout?**
- Increase timeout in `config/config.yaml`
- Reduce `--max-results`

### CSV Import Issues

**Import Errors?**
- Ensure CSV has an `email` column (required)
- Check column names match supported formats
- Verify CSV uses comma delimiter
- Check server logs for detailed error messages

## Key URLs

Once the web server is running:

- **Dashboard**: http://localhost:8080/
- **Campaigns**: http://localhost:8080/campaigns
- **Create Campaign**: http://localhost:8080/campaigns/create
- **Templates**: http://localhost:8080/templates
- **Create Template**: http://localhost:8080/templates/create
- **Leads**: http://localhost:8080/leads
- **Import Leads**: http://localhost:8080/leads/import

## Development

### Running in Development Mode

The web UI runs in debug mode by default:
```bash
python web_ui/app.py
```

### Running Queue Processor

To send queued emails in the background:
```bash
# Send once
python -m email_service.queue_processor --once

# Run continuously (checks every 60 seconds)
python -m email_service.queue_processor
```

### Database Management

```bash
# Initialize database
python scripts/db_manage.py init

# Reset database (WARNING: deletes all data)
python scripts/db_manage.py reset
```

## Support

- **Web UI Issues**: Check `web_ui/app.py` logs
- **Script Issues**: Check logs and verify configuration
- **Actor Issues**: https://console.apify.com/support
- **API Docs**: https://docs.apify.com/api/v2
- **Flask Docs**: https://flask.palletsprojects.com/

## License

Internal use only. Apify actors subject to their respective licenses.
