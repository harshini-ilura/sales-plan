# Web UI Guide - Bulk Email Sending

This guide explains how to access and use the web UI for sending bulk emails.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Web Server

```bash
python web_ui/app.py
```

The server will start on `http://localhost:8080` (default port changed to avoid macOS AirPlay conflict)

### 3. Access the Web UI

Open your browser and navigate to:
```
http://localhost:8080
```

**Note:** If you want to use a different port, set the `PORT` environment variable:
```bash
PORT=5000 python web_ui/app.py
```

## Workflow for Bulk Email Sending

### Step 1: Create an Email Template

1. Click **"Templates"** in the navigation bar
2. Click **"Create New Template"**
3. Fill in:
   - Template Name
   - Template Type (Initial Email, Follow-up Email, or Custom)
   - Email Subject (you can use variables like `{{first_name}}`, `{{company_name}}`)
   - Email Body (plain text and optionally HTML)
4. Click **"Create Template"**

### Step 2: Create a Campaign

1. Click **"Campaigns"** in the navigation bar
2. Click **"Create New Campaign"**
3. Fill in:
   - Campaign Name
   - Select the Email Template you created
   - Sender Email and Name
   - Optional: Target Filters (Country, Source)
   - Optional: Follow-up Settings
4. Click **"Create Campaign"**

### Step 3: Queue Emails for Sending

1. After creating a campaign, click **"View"** on the campaign
2. On the campaign detail page, you'll see a **"Queue Emails for Sending"** section
3. Choose options:
   - Check "Queue from latest run only" if you want to only queue new leads
   - Set a limit (optional) to limit how many emails to queue
4. Click **"Queue Emails for Sending"**

### Step 4: Process the Queue

The emails are now queued. You need to run the queue processor to actually send them:

```bash
python -m email_service.queue_processor
```

Or use the campaign manager script:
```bash
python scripts/email_campaign.py
```

## Navigation

- **Dashboard** (`/`) - Overview of campaigns, leads, and email statistics
- **Campaigns** (`/campaigns`) - List and manage email campaigns
- **Templates** (`/templates`) - Manage email templates
- **Leads** (`/leads`) - View your sales leads

## Features

- **Template Variables**: Use variables in your templates:
  - `{{first_name}}` - Lead's first name
  - `{{last_name}}` - Lead's last name
  - `{{full_name}}` - Lead's full name
  - `{{email}}` - Lead's email
  - `{{company_name}}` - Company name
  - `{{industry}}` - Industry
  - `{{city}}` - City
  - `{{country}}` - Country

- **Campaign Filtering**: Filter leads by:
  - Country
  - Source (Apify, Manual, Import)

- **Follow-up Emails**: Set up automatic follow-up emails that send after a specified number of days

## Troubleshooting

### Port Already in Use

The default port is now 8080 to avoid macOS AirPlay conflicts. If you need a different port, set the `PORT` environment variable:

```bash
PORT=5000 python web_ui/app.py
```

### Database Not Set Up

Make sure your database is initialized:

```bash
python scripts/db_manage.py init
```

### No Leads Found

Make sure you have imported leads into the database. You can scrape leads using:

```bash
python scripts/scrape_leads_apify.py --type email --locations chennai
```

## Notes

- The web UI runs in debug mode by default (useful for development)
- For production, change the `secret_key` in `web_ui/app.py`
- Emails are queued but not sent automatically - you need to run the queue processor separately

