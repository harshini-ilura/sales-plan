# Apify Lead Scraper

A production-ready Python implementation for scraping verified emails and phone numbers using Apify platform actors.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your API token
cp .env.example .env
# Edit .env and add your APIFY_API_TOKEN

# 3. Run your first scrape
python scripts/scrape_leads_apify.py --type email --locations chennai
```

## Features

- **Dual Actor Integration**: Combines email and phone number scrapers
- **Smart Filtering**: Filter by location, industry, company size, and type
- **Automatic Polling**: Waits for actor completion and retrieves results
- **Multiple Formats**: Export to JSON, CSV, or both
- **Data Management**: Built-in deduplication and merging
- **Production Ready**: Error handling, logging, and retry logic

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
├── config/
│   └── config.yaml           # Configuration
├── src/
│   ├── apify_client.py       # Core API client
│   ├── email_scraper.py      # Email scraper
│   ├── phone_scraper.py      # Phone scraper
│   └── data_manager.py       # Data management
├── scripts/
│   └── scrape_leads_apify.py # CLI interface
├── data/exports/             # Output directory
└── requirements.txt          # Dependencies
```

## Documentation

See [HOW_TO_RUN.md](HOW_TO_RUN.md) for:
- Detailed setup instructions
- Complete command reference
- API workflow explanation
- Troubleshooting guide
- Best practices

## Requirements

- Python 3.7+
- Apify API token
- Dependencies: `requests`, `python-dotenv`, `pyyaml`

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

## Support

- Script issues: Check logs and verify configuration
- Actor issues: https://console.apify.com/support
- API docs: https://docs.apify.com/api/v2

## License

Internal use only. Apify actors subject to their respective licenses.
