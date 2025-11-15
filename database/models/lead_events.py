"""
Lead Events model - tracks activities and changes for leads
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, AuditMixin


class LeadEvent(Base, AuditMixin):
    """
    Lead events table for tracking lead activities and changes
    """
    __tablename__ = 'lead_events'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Link to lead
    lead_id = Column(Integer, ForeignKey('sales_leads.id'), nullable=False, index=True)
    lead = relationship('SalesLead', back_populates='events')

    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # created, updated, contacted, enriched, etc.
    event_name = Column(String(255), nullable=False)
    event_description = Column(Text, nullable=True)

    # Event metadata
    event_data = Column(JSON, nullable=True)  # Flexible data storage
    event_source = Column(String(100), nullable=True)  # Where event originated

    # Timestamp (in addition to created_at from AuditMixin)
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Actor/User who triggered the event
    actor = Column(String(100), nullable=True)

    # Status change tracking
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)

    # Field change tracking (for update events)
    changed_fields = Column(JSON, nullable=True)  # {"field": {"old": value, "new": value}}

    def __repr__(self):
        return f"<LeadEvent(id={self.id}, lead_id={self.lead_id}, type='{self.event_type}')>"


# Indexes
Index('idx_event_lead_type', LeadEvent.lead_id, LeadEvent.event_type)
Index('idx_event_timestamp', LeadEvent.event_timestamp)
Index('idx_event_type_time', LeadEvent.event_type, LeadEvent.event_timestamp)
