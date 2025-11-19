"""
Email queue processor - processes pending emails from the queue
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_session
from database.models import EmailQueue, EmailCampaign, EmailTracking
from email_service.providers import get_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueueProcessor:
    """Process emails from the queue"""

    def __init__(
        self,
        provider_type: str = 'smtp',
        batch_size: int = 10,
        rate_limit: int = 100,  # emails per hour
        session: Optional[Session] = None,
        provider: Optional[Any] = None
    ):
        self.provider_type = provider_type
        self.provider = provider or get_provider(provider_type)
        self.batch_size = batch_size
        self.rate_limit = rate_limit
        self.session = session or get_session()
        self.emails_sent_this_hour = 0
        self.hour_start = datetime.utcnow()

    def get_pending_emails(self, limit: int = None) -> List[EmailQueue]:
        """Get pending emails from queue"""

        limit = limit or self.batch_size

        return self.session.query(EmailQueue).filter(
            and_(
                EmailQueue.status == 'pending',
                EmailQueue.scheduled_at <= datetime.utcnow(),
                EmailQueue.is_deleted == False
            )
        ).order_by(EmailQueue.scheduled_at).limit(limit).all()

    def check_rate_limit(self) -> bool:
        """Check if we've hit the rate limit"""

        # Reset counter if hour has passed
        now = datetime.utcnow()
        if (now - self.hour_start).total_seconds() >= 3600:
            self.emails_sent_this_hour = 0
            self.hour_start = now

        return self.emails_sent_this_hour < self.rate_limit

    def send_email(self, email: EmailQueue) -> bool:
        """Send a single email"""

        try:
            # Mark as sending
            email.status = 'sending'
            self.session.commit()

            # Send via provider
            result = self.provider.send(
                to_email=email.recipient_email,
                subject=email.subject,
                body_text=email.body_text,
                body_html=email.body_html,
                from_email=email.sender_email,
                from_name=email.sender_name,
                reply_to=email.campaign.reply_to if email.campaign else None,
                attachments=email.attachments
            )

            if result['success']:
                # Mark as sent
                email.mark_sent(provider_message_id=result.get('message_id'))
                email.provider = result.get('provider')

                # Update campaign stats
                if email.campaign:
                    email.campaign.emails_sent += 1

                # Create tracking event
                tracking = EmailTracking(
                    campaign_id=email.campaign_id,
                    email_id=email.id,
                    lead_id=email.lead_id,
                    event_type='sent',
                    event_timestamp=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.session.add(tracking)
                self.session.commit()

                logger.info(f"Sent email {email.id} to {email.recipient_email}")

                self.emails_sent_this_hour += 1
                return True

            else:
                # Mark as failed
                email.mark_failed(result.get('error', 'Unknown error'))

                # Update campaign stats
                if email.campaign:
                    email.campaign.emails_failed += 1

                self.session.commit()

                logger.error(f"Failed to send email {email.id}: {result.get('error')}")
                return False

        except Exception as e:
            email.mark_failed(str(e))

            if email.campaign:
                email.campaign.emails_failed += 1

            self.session.commit()

            logger.error(f"Exception sending email {email.id}: {e}")
            return False

    def process_batch(self) -> int:
        """Process a batch of pending emails"""

        emails = self.get_pending_emails()

        if not emails:
            logger.debug("No pending emails in queue")
            return 0

        sent_count = 0

        for email in emails:
            # Check rate limit
            if not self.check_rate_limit():
                logger.warning(f"Rate limit reached ({self.rate_limit}/hour). Pausing.")
                break

            # Send email
            if self.send_email(email):
                sent_count += 1

            # Small delay between emails
            time.sleep(0.5)

        logger.info(f"Processed batch: {sent_count}/{len(emails)} emails sent")
        return sent_count

    def process_retry_queue(self) -> int:
        """Process failed emails that can be retried"""

        retry_emails = self.session.query(EmailQueue).filter(
            and_(
                EmailQueue.status == 'failed',
                EmailQueue.retry_count < EmailQueue.max_retries,
                EmailQueue.is_deleted == False
            )
        ).limit(self.batch_size).all()

        if not retry_emails:
            return 0

        retry_count = 0

        for email in retry_emails:
            if not self.check_rate_limit():
                break

            # Reset status to pending
            email.status = 'pending'
            self.session.commit()

            # Try to send
            if self.send_email(email):
                retry_count += 1

            time.sleep(0.5)

        logger.info(f"Retried {retry_count} failed emails")
        return retry_count

    def run_once(self) -> dict:
        """Process one batch and return stats"""

        sent = self.process_batch()
        retried = self.process_retry_queue()

        return {
            'sent': sent,
            'retried': retried,
            'total': sent + retried
        }

    def run_continuous(self, interval: int = 60):
        """Run continuously, processing queue every interval seconds"""

        logger.info(f"Starting queue processor (provider={self.provider_type}, interval={interval}s)")

        try:
            while True:
                stats = self.run_once()

                if stats['total'] > 0:
                    logger.info(f"Processed {stats['total']} emails")

                # Wait before next iteration
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Queue processor stopped by user")
        finally:
            self.session.close()

    def close(self):
        """Close session"""
        self.session.close()


def main():
    """Main function for running queue processor"""
    import argparse

    parser = argparse.ArgumentParser(description='Email queue processor')
    parser.add_argument('--provider', default='smtp', choices=['smtp', 'sendgrid', 'aws_ses'],
                        help='Email provider to use')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size')
    parser.add_argument('--rate-limit', type=int, default=100, help='Emails per hour')
    parser.add_argument('--interval', type=int, default=60, help='Seconds between batches')
    parser.add_argument('--once', action='store_true', help='Process once and exit')

    args = parser.parse_args()

    processor = QueueProcessor(
        provider_type=args.provider,
        batch_size=args.batch_size,
        rate_limit=args.rate_limit
    )

    if args.once:
        stats = processor.run_once()
        print(f"Sent: {stats['sent']}, Retried: {stats['retried']}, Total: {stats['total']}")
    else:
        processor.run_continuous(interval=args.interval)


if __name__ == '__main__':
    main()
