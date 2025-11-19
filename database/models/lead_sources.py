"""
Lead Source model - tracks where each lead came from
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class LeadSource(BaseModel):
    """
    Lead source tracking table - one per lead
    """
    __tablename__ = 'lead_sources'

    # Link to lead
    lead_id = Column(Integer, ForeignKey('sales_leads.id'), nullable=False, unique=True)
    lead = relationship('SalesLead', back_populates='source_info')

    # Source details
    source_type = Column(String(50), nullable=False, index=True)  # 'apify', 'manual', 'import', 'api'
    source_name = Column(String(100), nullable=False)  # e.g., 'Apify Email Scraper'

    # Provider information
    provider_name = Column(String(100), nullable=False, default='apify')
    provider_id = Column(String(255), nullable=True)  # Provider's internal ID

    # Apify-specific fields
    actor_id = Column(String(100), nullable=True)
    actor_name = Column(String(255), nullable=True)
    run_id = Column(String(100), nullable=True)
    dataset_id = Column(String(100), nullable=True)

    # External identifiers
    external_id = Column(String(255), nullable=True)  # Unique ID from source system
    external_url = Column(String(500), nullable=True)  # URL to source record

    # Scrape/import metadata
    scraped_at = Column(DateTime, default=datetime.utcnow)
    import_batch_id = Column(String(100), nullable=True)  # For batch imports

    # Input parameters used for scraping (JSON)
    scrape_params = Column(JSON, nullable=True)

    # Quality metrics
    data_quality_score = Column(Integer, nullable=True)  # 0-100
    confidence_score = Column(Integer, nullable=True)  # 0-100

    # Additional metadata
    meta_data = Column('metadata', JSON, nullable=True)  # Using 'metadata' as DB column name, 'meta_data' as Python attr
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<LeadSource(id={self.id}, lead_id={self.lead_id}, source='{self.source_type}')>"


# Indexes
Index('idx_source_provider', LeadSource.provider_name, LeadSource.external_id)
Index('idx_source_actor_run', LeadSource.actor_id, LeadSource.run_id)
Index('idx_source_batch', LeadSource.import_batch_id)
