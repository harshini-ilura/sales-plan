"""
Email Template models
"""
from sqlalchemy import Column, String, Text, Integer, JSON, Boolean, Index
from sqlalchemy.orm import relationship
from .base import BaseModel


class EmailTemplate(BaseModel):
    """
    Email templates with variable substitution
    """
    __tablename__ = 'email_templates'

    # Template details
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Template type
    template_type = Column(String(50), nullable=False, default='initial')  # initial, follow_up, custom

    # Email content
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)  # HTML version
    body_text = Column(Text, nullable=False)  # Plain text version

    # Available variables for this template
    # e.g., ["{{first_name}}", "{{company_name}}", "{{industry}}"]
    available_variables = Column(JSON, nullable=True)

    # Template settings
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)

    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(String(50), nullable=True)

    # Metadata
    tags = Column(Text, nullable=True)
    meta_data = Column('metadata', JSON, nullable=True)  # Using 'metadata' as DB column name, 'meta_data' as Python attr

    # Relationships
    campaigns = relationship('EmailCampaign', back_populates='template', foreign_keys='EmailCampaign.template_id')

    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"

    def render(self, variables: dict) -> tuple:
        """
        Render template with variables

        Args:
            variables: Dictionary of variable values

        Returns:
            Tuple of (subject, body_html, body_text)
        """
        subject = self.subject
        body_html = self.body_html or self.body_text
        body_text = self.body_text

        # Simple variable substitution
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            if body_html:
                body_html = body_html.replace(placeholder, str(value))
            body_text = body_text.replace(placeholder, str(value))

        return subject, body_html, body_text


# Indexes
Index('idx_template_type_active', EmailTemplate.template_type, EmailTemplate.is_active)
