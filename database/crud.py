"""
CRUD operations for database models
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from .models import SalesLead, Company, LeadSource, ApifySyncState, LeadEvent


class LeadCRUD:
    """CRUD operations for SalesLead model"""

    @staticmethod
    def create(session: Session, **kwargs) -> SalesLead:
        """Create a new lead"""
        lead = SalesLead(**kwargs)
        session.add(lead)
        session.flush()

        # Create event (optional - don't fail if event creation fails)
        try:
            EventCRUD.create_event(
                session=session,
                lead_id=lead.id,
                event_type='created',
                event_name='Lead Created',
                event_description=f'Lead {lead.full_name or lead.email} created',
                actor=kwargs.get('created_by')
            )
        except Exception as e:
            # Log but don't fail lead creation if event creation fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create event for lead {lead.id}: {e}")

        return lead

    @staticmethod
    def get_by_id(session: Session, lead_id: int, include_deleted: bool = False) -> Optional[SalesLead]:
        """Get lead by ID"""
        query = session.query(SalesLead).filter(SalesLead.id == lead_id)
        if not include_deleted:
            query = query.filter(SalesLead.is_deleted == False)
        return query.first()

    @staticmethod
    def get_by_email(session: Session, email: str, include_deleted: bool = False) -> Optional[SalesLead]:
        """Get lead by email"""
        query = session.query(SalesLead).filter(SalesLead.email == email)
        if not include_deleted:
            query = query.filter(SalesLead.is_deleted == False)
        return query.first()

    @staticmethod
    def get_by_external_id(session: Session, provider: str, external_id: str) -> Optional[SalesLead]:
        """Get lead by provider and external ID"""
        return session.query(SalesLead).filter(
            and_(
                SalesLead.provider_name == provider,
                SalesLead.external_id == external_id,
                SalesLead.is_deleted == False
            )
        ).first()

    @staticmethod
    def list_leads(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> List[SalesLead]:
        """List leads with optional filters"""
        query = session.query(SalesLead)

        if not include_deleted:
            query = query.filter(SalesLead.is_deleted == False)

        if filters:
            if 'source' in filters:
                query = query.filter(SalesLead.source == filters['source'])
            if 'country' in filters:
                query = query.filter(SalesLead.country == filters['country'])
            if 'industry' in filters:
                query = query.filter(SalesLead.industry == filters['industry'])
            if 'lead_status' in filters:
                query = query.filter(SalesLead.lead_status == filters['lead_status'])
            if 'enrichment_status' in filters:
                query = query.filter(SalesLead.enrichment_status == filters['enrichment_status'])

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(session: Session, lead_id: int, updated_by: Optional[str] = None, **kwargs) -> Optional[SalesLead]:
        """Update a lead"""
        lead = LeadCRUD.get_by_id(session, lead_id)
        if not lead:
            return None

        # Track changes
        changed_fields = {}
        for key, value in kwargs.items():
            if hasattr(lead, key) and getattr(lead, key) != value:
                changed_fields[key] = {
                    'old': getattr(lead, key),
                    'new': value
                }
                setattr(lead, key, value)

        if updated_by:
            lead.updated_by = updated_by

        if changed_fields:
            # Create update event
            EventCRUD.create_event(
                session=session,
                lead_id=lead.id,
                event_type='updated',
                event_name='Lead Updated',
                event_description=f'Lead updated: {", ".join(changed_fields.keys())}',
                changed_fields=changed_fields,
                actor=updated_by
            )

        session.flush()
        return lead

    @staticmethod
    def delete(session: Session, lead_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a lead"""
        lead = LeadCRUD.get_by_id(session, lead_id)
        if not lead:
            return False

        lead.soft_delete(deleted_by=deleted_by)

        # Create event
        EventCRUD.create_event(
            session=session,
            lead_id=lead.id,
            event_type='deleted',
            event_name='Lead Deleted',
            event_description='Lead soft deleted',
            actor=deleted_by
        )

        session.flush()
        return True

    @staticmethod
    def restore(session: Session, lead_id: int) -> Optional[SalesLead]:
        """Restore a soft-deleted lead"""
        lead = LeadCRUD.get_by_id(session, lead_id, include_deleted=True)
        if lead and lead.is_deleted:
            lead.restore()
            session.flush()
        return lead

    @staticmethod
    def count(session: Session, filters: Optional[Dict[str, Any]] = None, include_deleted: bool = False) -> int:
        """Count leads"""
        query = session.query(SalesLead)

        if not include_deleted:
            query = query.filter(SalesLead.is_deleted == False)

        if filters:
            if 'source' in filters:
                query = query.filter(SalesLead.source == filters['source'])
            if 'country' in filters:
                query = query.filter(SalesLead.country == filters['country'])

        return query.count()


class CompanyCRUD:
    """CRUD operations for Company model"""

    @staticmethod
    def create(session: Session, **kwargs) -> Company:
        """Create a new company"""
        company = Company(**kwargs)
        session.add(company)
        session.flush()
        return company

    @staticmethod
    def get_by_id(session: Session, company_id: int) -> Optional[Company]:
        """Get company by ID"""
        return session.query(Company).filter(
            and_(Company.id == company_id, Company.is_deleted == False)
        ).first()

    @staticmethod
    def get_by_domain(session: Session, domain: str) -> Optional[Company]:
        """Get company by domain"""
        return session.query(Company).filter(
            and_(Company.domain == domain, Company.is_deleted == False)
        ).first()

    @staticmethod
    def get_or_create(session: Session, domain: str, **kwargs) -> Company:
        """Get existing company or create new one"""
        company = CompanyCRUD.get_by_domain(session, domain)
        if not company:
            company = CompanyCRUD.create(session, domain=domain, **kwargs)
        return company

    @staticmethod
    def update(session: Session, company_id: int, **kwargs) -> Optional[Company]:
        """Update a company"""
        company = CompanyCRUD.get_by_id(session, company_id)
        if not company:
            return None

        for key, value in kwargs.items():
            if hasattr(company, key):
                setattr(company, key, value)

        session.flush()
        return company


class LeadSourceCRUD:
    """CRUD operations for LeadSource model"""

    @staticmethod
    def create(session: Session, lead_id: int, **kwargs) -> LeadSource:
        """Create a new lead source"""
        source = LeadSource(lead_id=lead_id, **kwargs)
        session.add(source)
        session.flush()
        return source

    @staticmethod
    def get_by_lead_id(session: Session, lead_id: int) -> Optional[LeadSource]:
        """Get source by lead ID"""
        return session.query(LeadSource).filter(
            and_(LeadSource.lead_id == lead_id, LeadSource.is_deleted == False)
        ).first()


class ApifySyncCRUD:
    """CRUD operations for ApifySyncState model"""

    @staticmethod
    def create(session: Session, **kwargs) -> ApifySyncState:
        """Create a new sync state"""
        sync_state = ApifySyncState(**kwargs)
        session.add(sync_state)
        session.flush()
        return sync_state

    @staticmethod
    def get_by_run_id(session: Session, run_id: str) -> Optional[ApifySyncState]:
        """Get sync state by run ID"""
        return session.query(ApifySyncState).filter(
            ApifySyncState.run_id == run_id
        ).first()

    @staticmethod
    def update_status(session: Session, run_id: str, status: str, **kwargs) -> Optional[ApifySyncState]:
        """Update sync status"""
        sync_state = ApifySyncCRUD.get_by_run_id(session, run_id)
        if not sync_state:
            return None

        sync_state.sync_status = status
        sync_state.last_sync_at = datetime.utcnow()

        for key, value in kwargs.items():
            if hasattr(sync_state, key):
                setattr(sync_state, key, value)

        session.flush()
        return sync_state


class EventCRUD:
    """CRUD operations for LeadEvent model"""

    @staticmethod
    def create_event(
        session: Session,
        lead_id: int,
        event_type: str,
        event_name: str,
        event_description: Optional[str] = None,
        event_data: Optional[Dict] = None,
        actor: Optional[str] = None,
        **kwargs
    ) -> LeadEvent:
        """Create a new lead event"""
        event = LeadEvent(
            lead_id=lead_id,
            event_type=event_type,
            event_name=event_name,
            event_description=event_description,
            event_data=event_data,
            event_timestamp=datetime.utcnow(),
            actor=actor,
            created_by=actor,
            **kwargs
        )
        session.add(event)
        session.flush()
        return event

    @staticmethod
    def get_lead_events(session: Session, lead_id: int, limit: int = 50) -> List[LeadEvent]:
        """Get events for a lead"""
        return session.query(LeadEvent).filter(
            LeadEvent.lead_id == lead_id
        ).order_by(LeadEvent.event_timestamp.desc()).limit(limit).all()
