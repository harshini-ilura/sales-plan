"""
Email Campaign models for bulk email sending and lead enrichment
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, DateTime, Boolean, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import BaseModel


class CampaignStatus(enum.Enum):
    """Campaign status enum"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmailCampaign(BaseModel):
    """
    Email campaigns for organizing bulk email sends
    """
    __tablename__ = 'email_campaigns'

    # Campaign details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='draft', index=True)

    # Template reference
    template_id = Column(Integer, ForeignKey('email_templates.id'), nullable=True)
    template = relationship('EmailTemplate', back_populates='campaigns', foreign_keys=[template_id])

    # Targeting criteria (stored as JSON)
    target_filters = Column(JSON, nullable=True)  # e.g., {"country": "India", "source": "apify"}

    # Scheduling
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Follow-up configuration
    follow_up_enabled = Column(Boolean, default=False)
    follow_up_delay_days = Column(Integer, default=3)  # Days after initial email
    follow_up_template_id = Column(Integer, ForeignKey('email_templates.id'), nullable=True)

    # Sender information
    sender_name = Column(String(255), nullable=True)
    sender_email = Column(String(255), nullable=True)
    reply_to = Column(String(255), nullable=True)
    
    # Email provider configuration
    email_provider = Column(String(50), nullable=False, default='smtp')  # smtp, sendgrid, aws_ses
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_username = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)  # Should be encrypted in production
    
    # Attachments (stored as JSON array of file paths/metadata)
    attachments = Column(JSON, nullable=True)

    # Statistics
    total_recipients = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_delivered = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_failed = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)

    # Settings
    send_rate_limit = Column(Integer, default=100)  # Emails per hour

    # Metadata
    meta_data = Column('metadata', JSON, nullable=True)  # Using 'metadata' as DB column name, 'meta_data' as Python attr

    # Relationships
    queue_items = relationship('EmailQueue', back_populates='campaign', cascade='all, delete-orphan')
    tracking_events = relationship('EmailTracking', back_populates='campaign')

    def __repr__(self):
        return f"<EmailCampaign(id={self.id}, name='{self.name}', status='{self.status}')>"


# Indexes
Index('idx_campaign_status_scheduled', EmailCampaign.status, EmailCampaign.scheduled_at)
