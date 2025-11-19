"""
Email service providers (SMTP, SendGrid, AWS SES, etc.)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from pathlib import Path
from typing import Dict, Optional, Any, List
import logging
import os

logger = logging.getLogger(__name__)


class EmailProvider:
    """Base class for email providers"""

    def send(self, **kwargs) -> Dict[str, Any]:
        """
        Send email

        Returns:
            Dict with 'success' (bool) and 'message_id' (str) or 'error' (str)
        """
        raise NotImplementedError


class SMTPProvider(EmailProvider):
    """SMTP email provider"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True
    ):
        self.host = host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.port = port or int(os.getenv('SMTP_PORT', '587'))
        self.username = username or os.getenv('SMTP_USERNAME')
        self.password = password or os.getenv('SMTP_PASSWORD')
        self.use_tls = use_tls

    def send(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send email via SMTP"""

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['To'] = to_email

            # Set from address
            if from_email:
                if from_name:
                    msg['From'] = formataddr((from_name, from_email))
                else:
                    msg['From'] = from_email
            else:
                msg['From'] = self.username

            # Set reply-to
            if reply_to:
                msg['Reply-To'] = reply_to

            # Attach parts
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)

            if body_html:
                part2 = MIMEText(body_html, 'html')
                msg.attach(part2)

            # Attach files if provided
            if attachments:
                for attachment in attachments:
                    filepath = Path(attachment.get('path', attachment.get('filename', '')))
                    if filepath.exists():
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {filepath.name}'
                            )
                            msg.attach(part)

            # Connect and send
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.host, self.port)

            if self.username and self.password:
                server.login(self.username, self.password)

            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")

            return {
                'success': True,
                'message_id': msg['Message-ID'],
                'provider': 'smtp'
            }

        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'smtp'
            }


class SendGridProvider(EmailProvider):
    """SendGrid email provider (via API)"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')

        if self.api_key:
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                self.client = SendGridAPIClient(self.api_key)
                self.Mail = Mail
            except ImportError:
                logger.warning("SendGrid not installed. Run: pip install sendgrid")
                self.client = None

    def send(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send email via SendGrid"""

        if not self.client:
            return {
                'success': False,
                'error': 'SendGrid not configured',
                'provider': 'sendgrid'
            }

        try:
            message = self.Mail(
                from_email=(from_email or os.getenv('SENDER_EMAIL'), from_name),
                to_emails=to_email,
                subject=subject,
                plain_text_content=body_text,
                html_content=body_html or body_text
            )

            response = self.client.send(message)

            logger.info(f"Email sent via SendGrid to {to_email}")

            return {
                'success': True,
                'message_id': response.headers.get('X-Message-Id'),
                'status_code': response.status_code,
                'provider': 'sendgrid'
            }

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'sendgrid'
            }


class AWSProvider(EmailProvider):
    """AWS SES email provider"""

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = 'us-east-1'
    ):
        self.access_key = aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = region_name

        if self.access_key and self.secret_key:
            try:
                import boto3
                self.client = boto3.client(
                    'ses',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
            except ImportError:
                logger.warning("boto3 not installed. Run: pip install boto3")
                self.client = None

    def send(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        from_email: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send email via AWS SES"""

        if not self.client:
            return {
                'success': False,
                'error': 'AWS SES not configured',
                'provider': 'aws_ses'
            }

        try:
            response = self.client.send_email(
                Source=from_email or os.getenv('SENDER_EMAIL'),
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Text': {'Data': body_text},
                        'Html': {'Data': body_html or body_text}
                    }
                }
            )

            logger.info(f"Email sent via AWS SES to {to_email}")

            return {
                'success': True,
                'message_id': response['MessageId'],
                'provider': 'aws_ses'
            }

        except Exception as e:
            logger.error(f"Failed to send email via AWS SES: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'aws_ses'
            }


def get_provider(provider_type: str = 'smtp') -> EmailProvider:
    """
    Get email provider instance

    Args:
        provider_type: 'smtp', 'sendgrid', or 'aws_ses'

    Returns:
        EmailProvider instance
    """
    providers = {
        'smtp': SMTPProvider,
        'sendgrid': SendGridProvider,
        'aws_ses': AWSProvider
    }

    provider_class = providers.get(provider_type.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_type}")

    return provider_class()
