"""
Sales Lead model
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel


class SalesLead(BaseModel):
    """
    Sales leads table storing individual lead information
    """
    __tablename__ = 'sales_leads'

    # Lead identification
    full_name = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    title = Column(String(255), nullable=True)  # Job title

    # Contact information
    email = Column(String(255), nullable=True, index=True)
    email_verified = Column(String(50), nullable=True)  # verified, risky, unknown
    phone = Column(String(50), nullable=True, index=True)
    phone_verified = Column(String(50), nullable=True)

    # Additional contact methods (stored as JSON array)
    additional_emails = Column(JSON, nullable=True)
    additional_phones = Column(JSON, nullable=True)

    # Company relationship
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    company = relationship('Company', back_populates='leads')

    # Company info (denormalized for quick access)
    company_name = Column(String(255), nullable=True)
    company_domain = Column(String(255), nullable=True, index=True)

    # Geographic information
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Industry and tags
    industry = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)  # Comma-separated or JSON

    # Source tracking (Apify-specific)
    source = Column(String(50), nullable=False, index=True)  # 'apify', 'manual', 'import'
    provider_name = Column(String(100), nullable=False, default='apify')  # 'apify'
    external_id = Column(String(255), nullable=True)  # Unique ID from source
    actor_id = Column(String(100), nullable=True)  # Apify actor ID
    run_id = Column(String(100), nullable=True)  # Apify run ID
    dataset_id = Column(String(100), nullable=True)  # Apify dataset ID

    # Enrichment tracking
    enrichment_status = Column(String(50), default='pending')  # pending, enriched, failed
    enrichment_data = Column(JSON, nullable=True)  # Additional enriched data

    # Lead scoring and qualification
    lead_score = Column(Integer, nullable=True)
    lead_status = Column(String(50), default='new')  # new, contacted, qualified, converted

    # Additional metadata
    notes = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)  # Store original scraped data

    # Relationships
    events = relationship('LeadEvent', back_populates='lead', cascade='all, delete-orphan')
    source_info = relationship('LeadSource', back_populates='lead', uselist=False)

    def __repr__(self):
        return f"<SalesLead(id={self.id}, name='{self.full_name}', email='{self.email}')>"


# Composite indexes for common queries
Index('idx_provider_external', SalesLead.provider_name, SalesLead.external_id)
Index('idx_lead_source_actor', SalesLead.source, SalesLead.actor_id)
Index('idx_lead_location', SalesLead.country, SalesLead.city)
Index('idx_lead_status', SalesLead.lead_status, SalesLead.enrichment_status)
Index('idx_lead_company', SalesLead.company_id, SalesLead.lead_status)
