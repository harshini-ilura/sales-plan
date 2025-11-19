# How to Send Emails - Complete Guide

## Understanding Email Status

Emails go through these stages:
1. **Pending** - Emails are queued but not yet sent
2. **Sending** - Currently being processed
3. **Sent** - Successfully sent
4. **Failed** - Failed to send (can be retried)

## Two-Step Process

### Step 1: Queue Emails
This adds emails to the queue with "pending" status. It does NOT send them yet.

**In Web UI:**
1. Go to your campaign detail page
2. Click "Queue Emails" button
3. Emails are added to the queue

**Via Command Line:**
```bash
python scripts/email_campaign.py queue <campaign_id>
```

### Step 2: Send Emails
This actually sends the pending emails.

**In Web UI (NEW!):**
1. Go to your campaign detail page
2. Click "Send Pending Emails" button
3. Emails will be sent immediately

**Via Command Line:**
```bash
# Send emails once
python -m email_service.queue_processor --once

# Or run continuously (checks every 60 seconds)
python -m email_service.queue_processor
```

## Sending Emails from Web UI

### Quick Method (Recommended)

1. **Create Campaign** → `/campaigns/create`
   - Configure sender email and SMTP settings
   - Select template
   - Set targeting filters

2. **Queue Emails** → Go to campaign detail page
   - Click "Queue Emails" button
   - This adds emails to the queue

3. **Send Emails** → Same campaign detail page
   - Click "Send Pending Emails" button
   - Emails are sent immediately!

### What Happens When You Click "Send"

- Processes pending emails for that campaign
- Uses the campaign's configured email provider (SMTP/SendGrid/AWS SES)
- Uses campaign's SMTP credentials if configured
- Respects rate limits (default: 100 emails/hour)
- Updates status from "pending" → "sent" or "failed"
- Shows success/failure messages

## Command Line Method

### Send Once (One Batch)
```bash
python -m email_service.queue_processor --once --batch-size 10
```

### Run Continuously (Background Process)
```bash
# Process queue every 60 seconds
python -m email_service.queue_processor --interval 60

# With custom settings
python -m email_service.queue_processor \
  --provider smtp \
  --batch-size 20 \
  --rate-limit 200 \
  --interval 30
```

### Options:
- `--provider`: Email provider (smtp, sendgrid, aws_ses)
- `--batch-size`: Number of emails per batch (default: 10)
- `--rate-limit`: Emails per hour (default: 100)
- `--interval`: Seconds between batches (default: 60)
- `--once`: Process one batch and exit

## SMTP Configuration

For emails to actually send, you need SMTP credentials:

### Gmail Setup:
1. Enable 2-Factor Authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use in campaign form:
   - SMTP Host: `smtp.gmail.com`
   - SMTP Port: `587`
   - SMTP Username: `your-email@gmail.com`
   - SMTP Password: `your-app-password`

### Other Providers:
- **Outlook**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom SMTP**: Use your provider's settings

## Troubleshooting

### Emails Stay "Pending"
- **Solution**: Click "Send Pending Emails" button or run queue processor

### Emails Show "Failed"
- Check SMTP credentials are correct
- Verify sender email has permission to send
- Check rate limits aren't exceeded
- Review error messages in campaign detail page

### No Emails Queued
- Make sure you have leads in the database
- Check campaign filters match your leads
- Verify leads have email addresses

### SMTP Authentication Errors
- For Gmail: Use App Password, not regular password
- Check SMTP host and port are correct
- Verify username matches sender email

## Best Practices

1. **Test First**: Queue and send 1-2 emails to test
2. **Rate Limits**: Don't exceed provider limits (Gmail: ~500/day)
3. **Batch Size**: Start with 10-20 emails per batch
4. **Monitor**: Check campaign stats after sending
5. **Retry Failed**: Failed emails can be retried automatically

## Automatic Sending (Optional)

To automatically send emails in the background:

```bash
# Run in background or as a service
nohup python -m email_service.queue_processor --interval 60 > queue.log 2>&1 &
```

Or use a process manager like `supervisord` or `systemd` for production.

## Summary

**Quick Answer**: 
- Emails stay "pending" until you click "Send Pending Emails" button
- Or run: `python -m email_service.queue_processor --once`
- The web UI now has a "Send" button for instant sending!

