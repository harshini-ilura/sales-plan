"""
Email Queue models for managing email sending
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class EmailQueue(BaseModel):
    """
    Queue for emails to be sent
    """
    __tablename__ = 'email_queue'

    # Campaign reference
    campaign_id = Column(Integer, ForeignKey('email_campaigns.id'), nullable=False, index=True)
    campaign = relationship('EmailCampaign', back_populates='queue_items')

    # Lead reference
    lead_id = Column(Integer, ForeignKey('sales_leads.id'), nullable=False, index=True)
    lead = relationship('SalesLead')

    # Email details
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255), nullable=True)

    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(255), nullable=True)

    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=False)

    # Scheduling
    scheduled_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    sent_at = Column(DateTime, nullable=True)

    # Status tracking
    status = Column(String(50), nullable=False, default='pending', index=True)
    # pending, sending, sent, failed, bounced, cancelled

    # Email type
    email_type = Column(String(50), default='initial')  # initial, follow_up
    parent_email_id = Column(Integer, ForeignKey('email_queue.id'), nullable=True)  # For follow-ups

    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text, nullable=True)

    # Provider tracking
    provider = Column(String(50), nullable=True)  # smtp, sendgrid, ses, etc.
    provider_message_id = Column(String(255), nullable=True, index=True)

    # Metadata
    variables = Column(JSON, nullable=True)  # Variables used for rendering
    meta_data = Column('metadata', JSON, nullable=True)  # Using 'metadata' as DB column name, 'meta_data' as Python attr
    
    # Attachments (stored as JSON array of file paths/metadata)
    attachments = Column(JSON, nullable=True)

    # Relationships
    tracking_events = relationship('EmailTracking', back_populates='email')

    def __repr__(self):
        return f"<EmailQueue(id={self.id}, to='{self.recipient_email}', status='{self.status}')>"

    def can_retry(self) -> bool:
        """Check if email can be retried"""
        return self.retry_count < self.max_retries and self.status == 'failed'

    def mark_sent(self, provider_message_id: str = None):
        """Mark email as sent"""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()
        if provider_message_id:
            self.provider_message_id = provider_message_id

    def mark_failed(self, error: str):
        """Mark email as failed"""
        self.status = 'failed'
        self.last_error = error
        self.retry_count += 1


# Indexes
Index('idx_queue_status_scheduled', EmailQueue.status, EmailQueue.scheduled_at)
Index('idx_queue_campaign_status', EmailQueue.campaign_id, EmailQueue.status)
Index('idx_queue_lead', EmailQueue.lead_id)
Index('idx_queue_provider_message', EmailQueue.provider_message_id)
