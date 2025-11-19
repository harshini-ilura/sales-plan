"""
Email Tracking models for analytics
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, AuditMixin


class EmailTracking(Base, AuditMixin):
    """
    Track email events (opens, clicks, bounces, etc.)
    """
    __tablename__ = 'email_tracking'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # References
    campaign_id = Column(Integer, ForeignKey('email_campaigns.id'), nullable=False, index=True)
    campaign = relationship('EmailCampaign', back_populates='tracking_events')

    email_id = Column(Integer, ForeignKey('email_queue.id'), nullable=False, index=True)
    email = relationship('EmailQueue', back_populates='tracking_events')

    lead_id = Column(Integer, ForeignKey('sales_leads.id'), nullable=True, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    # sent, delivered, opened, clicked, bounced, failed, replied, unsubscribed

    event_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Event data
    event_data = Column(JSON, nullable=True)
    # For 'clicked': {"url": "https://..."}
    # For 'bounced': {"bounce_type": "hard", "reason": "..."}
    # For 'failed': {"error": "..."}

    # Provider info
    provider_event_id = Column(String(255), nullable=True)

    # User agent / IP (for opens/clicks)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)

    # Location (if available)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    # Metadata
    meta_data = Column('metadata', JSON, nullable=True)  # Using 'metadata' as DB column name, 'meta_data' as Python attr

    def __repr__(self):
        return f"<EmailTracking(id={self.id}, type='{self.event_type}', email_id={self.email_id})>"


# Indexes
Index('idx_tracking_campaign_event', EmailTracking.campaign_id, EmailTracking.event_type)
Index('idx_tracking_email_event', EmailTracking.email_id, EmailTracking.event_type)
Index('idx_tracking_event_time', EmailTracking.event_type, EmailTracking.event_timestamp)
Index('idx_tracking_lead', EmailTracking.lead_id)
