"""
Company model
"""
from sqlalchemy import Column, String, Text, Integer, Index
from sqlalchemy.orm import relationship
from .base import BaseModel


class Company(BaseModel):
    """
    Company table storing unique company information
    """
    __tablename__ = 'companies'

    # Company identification
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True, index=True)
    company_type = Column(String(50), nullable=True)  # PRIVATE, PUBLIC, etc.

    # Location
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)

    # Company details
    industry = Column(String(100), nullable=True, index=True)
    employee_count = Column(Integer, nullable=True)
    employee_size_min = Column(Integer, nullable=True)
    employee_size_max = Column(Integer, nullable=True)

    # Additional information
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)

    # Tags as JSON or comma-separated
    tags = Column(Text, nullable=True)

    # Relationships
    leads = relationship('SalesLead', back_populates='company')

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', domain='{self.domain}')>"


# Composite indexes
Index('idx_company_location', Company.country, Company.city)
Index('idx_company_industry_country', Company.industry, Company.country)
