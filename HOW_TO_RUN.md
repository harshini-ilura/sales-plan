# Apify Lead Scraper - User Guide

A comprehensive lead scraping solution that integrates two Apify actors for extracting verified emails and phone numbers from companies.

## Features

- **Email Scraper**: Extract verified emails using Apify actor `T1XDXWc1L92AfIJtd`
- **Phone Scraper**: Extract phone numbers and company data using Apify actor `aihL2lJmGDt9XFCGg`
- **Flexible Filtering**: Filter by location, industry, company size, and company type
- **Multiple Export Formats**: Save results as JSON, CSV, or both
- **Data Management**: Built-in deduplication and merging capabilities
- **Automatic Status Polling**: Waits for actor completion and retrieves results automatically

## Project Structure

```
sales-plan/
├── config/
│   └── config.yaml           # Actor and API configuration
├── src/
│   ├── apify_client.py       # Core Apify API integration
│   ├── email_scraper.py      # Email scraper implementation
│   ├── phone_scraper.py      # Phone scraper implementation
│   └── data_manager.py       # Data storage and export
├── scripts/
│   └── scrape_leads_apify.py # CLI interface
├── data/
│   └── exports/              # Exported data files
├── .env                      # Your API token (create this)
├── .env.example              # Example environment file
└── requirements.txt          # Python dependencies
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Token

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Apify API token:

```
APIFY_API_TOKEN=your_actual_token_here
```

Get your token from: https://console.apify.com/account/integrations

### 3. Verify Setup

```bash
python scripts/scrape_leads_apify.py --help
```

## Usage Examples

### Basic Usage

#### Scrape Emails

```bash
python scripts/scrape_leads_apify.py --type email \
  --locations chennai
```

#### Scrape Phone Numbers

```bash
python scripts/scrape_leads_apify.py --type phone \
  --locations dubai
```

#### Scrape Both Emails and Phone Numbers

```bash
python scripts/scrape_leads_apify.py --type both \
  --locations chennai dubai
```

### Advanced Filtering

#### Filter by Industry

```bash
python scripts/scrape_leads_apify.py --type phone \
  --locations dubai \
  --industries software technology "IT Services"
```

#### Filter by Company Size

```bash
python scripts/scrape_leads_apify.py --type email \
  --locations chennai \
  --employee-min 50 \
  --employee-max 500
```

#### Filter by Company Type

```bash
python scripts/scrape_leads_apify.py --type phone \
  --locations dubai \
  --company-types PRIVATE PUBLIC
```

#### Comprehensive Example

```bash
python scripts/scrape_leads_apify.py --type both \
  --locations chennai dubai bangalore \
  --industries software technology \
  --employee-min 10 \
  --employee-max 1000 \
  --max-results 200 \
  --output tech_companies \
  --format both
```

### Output Options

#### Save as JSON Only

```bash
python scripts/scrape_leads_apify.py --type email \
  --locations chennai \
  --format json
```

#### Save as CSV Only

```bash
python scripts/scrape_leads_apify.py --type phone \
  --locations dubai \
  --format csv
```

#### Custom Output Filename

```bash
python scripts/scrape_leads_apify.py --type email \
  --locations chennai \
  --output my_leads \
  --no-timestamp
```

This creates `data/exports/my_leads.json` and `data/exports/my_leads.csv`

## Command Line Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--type` | Yes | Type of scraping: `email`, `phone`, or `both` | - |
| `--locations` | Yes | Organization locations (space-separated) | - |
| `--industries` | No | Industries to filter by | None |
| `--company-types` | No | Company types (e.g., PRIVATE, PUBLIC) | `PRIVATE` |
| `--employee-min` | No | Minimum employee count | `0` |
| `--employee-max` | No | Maximum employee count | None |
| `--max-results` | No | Maximum number of results | `100` |
| `--output` | No | Output filename (without extension) | Auto-generated |
| `--format` | No | Output format: `json`, `csv`, or `both` | `both` |
| `--no-timestamp` | No | Don't include timestamp in filename | False |
| `--token` | No | Apify API token (overrides .env) | From .env |

## Understanding the Actors

### Email Scraper Actor (T1XDXWc1L92AfIJtd)

**Purpose**: Extracts verified email addresses from organizations

**Input Parameters**:
```json
{
  "getEmails": true,
  "includeRiskyEmails": true,
  "maxResults": 100,
  "organizationLocations": ["chennai"],
  "industries": ["software"],
  "employeeSizeMin": 0
}
```

### Phone Scraper Actor (aihL2lJmGDt9XFCGg)

**Purpose**: Extracts phone numbers and company information

**Input Parameters**:
```json
{
  "companyTypes": ["PRIVATE"],
  "employeeSizeMin": 0,
  "getEmails": true,
  "includeRiskyEmails": true,
  "industries": ["software"],
  "maxResults": 100,
  "organizationLocations": ["dubai"]
}
```

## API Workflow

1. **Start Actor Run**: POST to `/v2/acts/{actorId}/runs` with input parameters
2. **Poll Status**: GET `/v2/actor-runs/{runId}` to check status
3. **Wait for Completion**: Script automatically polls until status is `SUCCEEDED`
4. **Retrieve Results**: GET `/v2/datasets/{datasetId}/items` to fetch data
5. **Save Locally**: Export to JSON/CSV in `data/exports/`

## Output Format

### Sample JSON Output

```json
[
  {
    "email": "contact@example.com",
    "phone": "+971-xxx-xxxxx",
    "companyName": "Example Tech Co",
    "location": "Dubai",
    "industry": "Software",
    "employeeCount": 150,
    "companyType": "PRIVATE"
  }
]
```

### Sample CSV Output

```
email,phone,companyName,location,industry,employeeCount,companyType
contact@example.com,+971-xxx-xxxxx,Example Tech Co,Dubai,Software,150,PRIVATE
```

## Programmatic Usage

You can also use the modules directly in Python:

```python
from src.email_scraper import EmailScraper
from src.phone_scraper import PhoneScraper
from src.data_manager import DataManager

# Scrape emails
email_scraper = EmailScraper()
run_data, results = email_scraper.scrape(
    organization_locations=["chennai"],
    max_results=100
)

# Scrape phones
phone_scraper = PhoneScraper()
run_data, results = phone_scraper.scrape(
    organization_locations=["dubai"],
    industries=["software"],
    max_results=100
)

# Save results
data_manager = DataManager()
data_manager.save_both_formats(results, filename="my_leads")
```

## Configuration

Edit `config/config.yaml` to customize:

- Default actor parameters
- API timeout and polling settings
- Export formats and directories

## Troubleshooting

### API Token Not Found

```
Error: APIFY_API_TOKEN not found.
```

**Solution**: Create `.env` file with your token or pass via `--token` argument

### Actor Run Failed

Check the Apify console for run details:
```
https://console.apify.com/actors/runs/{runId}
```

### No Results Found

- Verify location names are correct
- Try broader filters (remove industry constraints)
- Increase `--max-results`
- Check if actor has data for your specified criteria

### Timeout Issues

Increase timeout in `config/config.yaml`:

```yaml
api:
  timeout: 600  # 10 minutes
```

## Cost Considerations

Both actors use pay-per-event pricing. From the example response:

```json
"pricingPerEvent": {
  "output_record": {
    "eventTitle": "Results",
    "eventDescription": "price per 1000 results ranges from $1.4 to $1.9",
    "eventPriceUsd": 0.00199
  }
}
```

Cost per result: ~$0.002 USD

## Best Practices

1. **Start Small**: Test with `--max-results 10` first
2. **Use Filters**: Narrow down by industry/location to get relevant leads
3. **Check Pricing**: Monitor usage at https://console.apify.com/billing
4. **Save Incrementally**: Run multiple small batches instead of one large batch
5. **Deduplicate**: When merging datasets, use `--type both` for automatic deduplication

## Support

For issues with:
- **This script**: Check error logs and verify configuration
- **Apify actors**: Visit https://console.apify.com/support
- **Actor pricing**: Check https://console.apify.com/billing

## License

This project is for internal use. Apify actors are subject to their respective licenses.
