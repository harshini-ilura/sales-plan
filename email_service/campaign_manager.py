"""
Campaign management - create campaigns, queue emails from leads
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_session
from database.models import (
    EmailCampaign, EmailTemplate, EmailQueue, SalesLead,
    ApifySyncState
)

logger = logging.getLogger(__name__)


class CampaignManager:
    """Manage email campaigns"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()

    def create_template(
        self,
        name: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        template_type: str = 'initial',
        **kwargs
    ) -> EmailTemplate:
        """Create an email template"""

        template = EmailTemplate(
            name=name,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            template_type=template_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs
        )

        self.session.add(template)
        self.session.commit()

        logger.info(f"Created template: {name}")
        return template

    def update_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        subject: Optional[str] = None,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        template_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        **kwargs
    ) -> Optional[EmailTemplate]:
        """Update an email template"""

        template = self.session.query(EmailTemplate).filter(
            EmailTemplate.id == template_id,
            EmailTemplate.is_deleted == False
        ).first()

        if not template:
            return None

        if name is not None:
            template.name = name
        if subject is not None:
            template.subject = subject
        if body_text is not None:
            template.body_text = body_text
        if body_html is not None:
            template.body_html = body_html
        if template_type is not None:
            template.template_type = template_type
        if is_active is not None:
            template.is_active = is_active

        template.updated_at = datetime.utcnow()

        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)

        self.session.commit()

        logger.info(f"Updated template: {template.name}")
        return template

    def create_campaign(
        self,
        name: str,
        template_id: int,
        sender_email: str,
        sender_name: Optional[str] = None,
        description: Optional[str] = None,
        target_filters: Optional[Dict] = None,
        follow_up_enabled: bool = False,
        follow_up_delay_days: int = 3,
        follow_up_template_id: Optional[int] = None,
        email_provider: str = 'smtp',
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        reply_to: Optional[str] = None,
        send_rate_limit: int = 100,
        **kwargs
    ) -> EmailCampaign:
        """Create an email campaign"""

        campaign = EmailCampaign(
            name=name,
            description=description,
            template_id=template_id,
            sender_email=sender_email,
            sender_name=sender_name,
            reply_to=reply_to,
            target_filters=target_filters,
            follow_up_enabled=follow_up_enabled,
            follow_up_delay_days=follow_up_delay_days,
            follow_up_template_id=follow_up_template_id,
            email_provider=email_provider,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            attachments=attachments,
            send_rate_limit=send_rate_limit,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs
        )

        self.session.add(campaign)
        self.session.commit()

        logger.info(f"Created campaign: {name}")
        return campaign

    def get_recent_leads(
        self,
        limit: int = 100,
        filters: Optional[Dict] = None,
        from_run_id: Optional[str] = None
    ) -> List[SalesLead]:
        """
        Get recent leads from database

        Args:
            limit: Maximum number of leads
            filters: Filter criteria (country, source, etc.)
            from_run_id: Get leads from specific Apify run

        Returns:
            List of SalesLead objects
        """

        query = self.session.query(SalesLead).filter(
            and_(
                SalesLead.is_deleted == False,
                SalesLead.email.isnot(None)
            )
        )

        # Filter by run ID if specified
        if from_run_id:
            query = query.filter(SalesLead.run_id == from_run_id)

        # Apply additional filters
        if filters:
            if 'country' in filters:
                query = query.filter(SalesLead.country == filters['country'])
            if 'source' in filters:
                query = query.filter(SalesLead.source == filters['source'])
            if 'industry' in filters:
                query = query.filter(SalesLead.industry == filters['industry'])
            if 'lead_status' in filters:
                query = query.filter(SalesLead.lead_status == filters['lead_status'])

        # Order by most recent first
        query = query.order_by(desc(SalesLead.created_at))

        leads = query.limit(limit).all()

        logger.info(f"Retrieved {len(leads)} leads")
        return leads

    def get_latest_run_id(self, actor_id: Optional[str] = None) -> Optional[str]:
        """Get the most recent Apify run ID"""

        query = self.session.query(ApifySyncState).filter(
            ApifySyncState.sync_status == 'completed'
        )

        if actor_id:
            query = query.filter(ApifySyncState.actor_id == actor_id)

        sync_state = query.order_by(desc(ApifySyncState.last_sync_at)).first()

        if sync_state:
            logger.info(f"Latest run ID: {sync_state.run_id}")
            return sync_state.run_id

        return None

    def queue_campaign(
        self,
        campaign_id: int,
        leads: Optional[List[SalesLead]] = None,
        scheduled_at: Optional[datetime] = None
    ) -> int:
        """
        Queue emails for a campaign

        Args:
            campaign_id: Campaign ID
            leads: List of leads (if None, uses campaign filters)
            scheduled_at: When to send (default: now)

        Returns:
            Number of emails queued
        """

        campaign = self.session.query(EmailCampaign).get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if not campaign.template:
            raise ValueError("Campaign has no template")

        # Get leads if not provided
        if leads is None:
            leads = self.get_recent_leads(
                limit=1000,
                filters=campaign.target_filters
            )

        if not leads:
            logger.warning("No leads found to queue")
            return 0

        scheduled_at = scheduled_at or datetime.utcnow()

        queued_count = 0

        for lead in leads:
            if not lead.email:
                continue

            # Check if already queued for this campaign
            existing = self.session.query(EmailQueue).filter(
                and_(
                    EmailQueue.campaign_id == campaign_id,
                    EmailQueue.lead_id == lead.id,
                    EmailQueue.status.in_(['pending', 'sent'])
                )
            ).first()

            if existing:
                logger.debug(f"Lead {lead.id} already queued for campaign {campaign_id}")
                continue

            # Prepare template variables
            variables = {
                'first_name': lead.first_name or lead.full_name or 'there',
                'last_name': lead.last_name or '',
                'full_name': lead.full_name or '',
                'email': lead.email,
                'company_name': lead.company_name or '',
                'industry': lead.industry or '',
                'city': lead.city or '',
                'country': lead.country or ''
            }

            # Render template
            subject, body_html, body_text = campaign.template.render(variables)

            # Create queue item
            email = EmailQueue(
                campaign_id=campaign_id,
                lead_id=lead.id,
                recipient_email=lead.email,
                recipient_name=lead.full_name,
                sender_email=campaign.sender_email,
                sender_name=campaign.sender_name,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                scheduled_at=scheduled_at,
                email_type='initial',
                variables=variables,
                attachments=campaign.attachments,  # Copy attachments from campaign
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(email)
            queued_count += 1

        # Update campaign
        campaign.total_recipients = queued_count
        campaign.status = 'scheduled'

        self.session.commit()

        logger.info(f"Queued {queued_count} emails for campaign {campaign.name}")
        return queued_count

    def queue_from_latest_run(
        self,
        campaign_id: int,
        actor_id: Optional[str] = None,
        limit: int = 100
    ) -> int:
        """
        Queue emails from the latest Apify run

        Args:
            campaign_id: Campaign ID
            actor_id: Filter by specific actor (optional)
            limit: Maximum leads to queue

        Returns:
            Number of emails queued
        """

        # Get latest run ID
        run_id = self.get_latest_run_id(actor_id=actor_id)

        if not run_id:
            logger.warning("No completed runs found")
            return 0

        # Get leads from that run
        leads = self.get_recent_leads(
            limit=limit,
            from_run_id=run_id
        )

        # Queue the campaign
        return self.queue_campaign(campaign_id=campaign_id, leads=leads)

    def schedule_follow_ups(self, campaign_id: int) -> int:
        """
        Schedule follow-up emails for a campaign

        Args:
            campaign_id: Campaign ID

        Returns:
            Number of follow-ups scheduled
        """

        campaign = self.session.query(EmailCampaign).get(campaign_id)

        if not campaign or not campaign.follow_up_enabled:
            return 0

        if not campaign.follow_up_template_id:
            logger.warning(f"Campaign {campaign_id} has no follow-up template")
            return 0

        # Get sent emails from this campaign
        sent_emails = self.session.query(EmailQueue).filter(
            and_(
                EmailQueue.campaign_id == campaign_id,
                EmailQueue.status == 'sent',
                EmailQueue.email_type == 'initial'
            )
        ).all()

        follow_up_template = self.session.query(EmailTemplate).get(campaign.follow_up_template_id)

        scheduled_count = 0

        for sent_email in sent_emails:
            # Check if follow-up already queued
            existing_follow_up = self.session.query(EmailQueue).filter(
                and_(
                    EmailQueue.parent_email_id == sent_email.id,
                    EmailQueue.status.in_(['pending', 'sent'])
                )
            ).first()

            if existing_follow_up:
                continue

            # Schedule follow-up
            follow_up_date = sent_email.sent_at + timedelta(days=campaign.follow_up_delay_days)

            # Render template
            subject, body_html, body_text = follow_up_template.render(sent_email.variables or {})

            follow_up = EmailQueue(
                campaign_id=campaign_id,
                lead_id=sent_email.lead_id,
                recipient_email=sent_email.recipient_email,
                recipient_name=sent_email.recipient_name,
                sender_email=campaign.sender_email,
                sender_name=campaign.sender_name,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                scheduled_at=follow_up_date,
                email_type='follow_up',
                parent_email_id=sent_email.id,
                variables=sent_email.variables,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(follow_up)
            scheduled_count += 1

        self.session.commit()

        logger.info(f"Scheduled {scheduled_count} follow-up emails")
        return scheduled_count

    def get_campaign_stats(self, campaign_id: int) -> Dict[str, Any]:
        """Get campaign statistics"""

        campaign = self.session.query(EmailCampaign).get(campaign_id)

        if not campaign:
            return {}

        return {
            'campaign_id': campaign.id,
            'name': campaign.name,
            'status': campaign.status,
            'total_recipients': campaign.total_recipients,
            'emails_sent': campaign.emails_sent,
            'emails_delivered': campaign.emails_delivered,
            'emails_opened': campaign.emails_opened,
            'emails_clicked': campaign.emails_clicked,
            'emails_failed': campaign.emails_failed,
            'open_rate': f"{(campaign.emails_opened/campaign.emails_sent*100):.1f}%" if campaign.emails_sent > 0 else "0%",
            'click_rate': f"{(campaign.emails_clicked/campaign.emails_sent*100):.1f}%" if campaign.emails_sent > 0 else "0%",
            'created_at': campaign.created_at,
            'started_at': campaign.started_at,
            'completed_at': campaign.completed_at
        }

    def close(self):
        """Close session"""
        self.session.close()
