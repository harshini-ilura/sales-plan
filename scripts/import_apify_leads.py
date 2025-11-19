#!/usr/bin/env python3
"""
Import Apify scraping results into the database
"""
import sys
import os
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import session_scope
from database.crud import LeadCRUD, LeadSourceCRUD, ApifySyncCRUD, CompanyCRUD
from src.data_manager import DataManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to Python datetime object"""
    if not date_str:
        return None
    
    try:
        # Handle ISO format with timezone (e.g., '2025-11-18T03:08:29.113Z')
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        try:
            # Try parsing common formats
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
        logger.warning(f"Could not parse datetime: {date_str}")
        return None


def normalize_name(full_name: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Split full name into first and last name"""
    if not full_name:
        return None, None
    
    parts = full_name.strip().split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


def map_apify_result_to_lead(result: Dict[str, Any], run_data: Dict[str, Any], actor_id: str) -> Dict[str, Any]:
    """
    Map Apify result to SalesLead fields
    
    Args:
        result: Apify result record
        run_data: Apify run metadata
        actor_id: Apify actor ID
        
    Returns:
        Dictionary with lead fields
    """
    # Skip invalid records (like log messages)
    if not isinstance(result, dict) or not result.get('email'):
        return None
    
    # Extract name - handle both firstName/lastName and fullName
    first_name = result.get('firstName')
    last_name = result.get('lastName')
    full_name = result.get('fullName')
    
    if not full_name and (first_name or last_name):
        full_name = f"{first_name or ''} {last_name or ''}".strip()
    
    if not first_name and not last_name and full_name:
        first_name, last_name = normalize_name(full_name)
    
    # Extract email
    email = result.get('email')
    if not email:
        return None  # Skip records without email
    
    email_verified = None
    if email:
        # Check if email is verified (Apify sometimes includes this)
        if result.get('emailVerified') or result.get('verified'):
            email_verified = 'verified'
        elif result.get('riskyEmail'):
            email_verified = 'risky'
        else:
            email_verified = 'unknown'
    
    # Extract phone
    phone = result.get('phone') or result.get('phoneNumber') or result.get('telephone')
    
    # Extract company info - handle organizationName, organizationWebsite
    company_name = result.get('organizationName') or result.get('companyName') or result.get('company')
    company_domain = result.get('organizationWebsite') or result.get('domain') or result.get('website')
    
    # Clean up domain
    if company_domain:
        # Remove http://, https://, www.
        company_domain = company_domain.replace('https://', '').replace('http://', '').replace('www.', '')
        # Remove trailing slash
        company_domain = company_domain.rstrip('/')
        # Extract domain from full URL if needed
        if '/' in company_domain:
            company_domain = company_domain.split('/')[0]
    
    # Extract location - handle organizationCity, organizationCountry
    city = result.get('organizationCity') or result.get('city') or result.get('location')
    country = result.get('organizationCountry') or result.get('country')
    state = result.get('organizationState') or result.get('state')
    
    # Extract industry
    industry = result.get('organizationIndustry') or result.get('industry') or result.get('industries')
    if isinstance(industry, list):
        industry = industry[0] if industry else None
    
    # Extract position/title
    title = result.get('position') or result.get('title')
    
    # Extract external ID - use LinkedIn URL or email as fallback
    external_id = result.get('linkedinUrl') or result.get('id') or result.get('externalId') or email
    
    # Build lead data
    lead_data = {
        'full_name': full_name,
        'first_name': first_name,
        'last_name': last_name,
        'title': title,
        'email': email,
        'email_verified': email_verified,
        'phone': phone,
        'company_name': company_name,
        'company_domain': company_domain,
        'country': country,
        'city': city,
        'state': state,
        'industry': industry,
        'source': 'apify',
        'provider_name': 'apify',
        'actor_id': actor_id,
        'run_id': run_data.get('id'),
        'dataset_id': run_data.get('defaultDatasetId'),
        'external_id': external_id,
        'raw_data': result
    }
    
    return lead_data


def import_leads_to_database(
    results: List[Dict[str, Any]],
    run_data: Dict[str, Any],
    actor_id: str,
    actor_name: Optional[str] = None,
    scrape_params: Optional[Dict[str, Any]] = None
) -> Dict[str, int]:
    """
    Import Apify results into the database
    
    Args:
        results: List of Apify result records
        run_data: Apify run metadata
        actor_id: Apify actor ID
        actor_name: Actor name (optional)
        scrape_params: Scraping parameters used (optional)
        
    Returns:
        Dictionary with import statistics
    """
    stats = {
        'total': len(results),
        'imported': 0,
        'skipped': 0,
        'errors': 0
    }
    
    run_id = run_data.get('id')
    
    with session_scope() as session:
        # Create or update sync state
        sync_state = ApifySyncCRUD.get_by_run_id(session, run_id)
        if not sync_state:
            # Parse datetime strings to datetime objects
            started_at = parse_datetime(run_data.get('startedAt'))
            finished_at = parse_datetime(run_data.get('finishedAt'))
            
            sync_state = ApifySyncCRUD.create(
                session=session,
                actor_id=actor_id,
                actor_name=actor_name or f'Actor {actor_id}',
                run_id=run_id,
                dataset_id=run_data.get('defaultDatasetId'),
                run_status=run_data.get('status'),
                started_at=started_at,
                finished_at=finished_at,
                input_params=scrape_params,
                total_records=len(results),
                sync_status='syncing'
            )
        else:
            sync_state.sync_status = 'syncing'
            sync_state.total_records = len(results)
        
        # Import each result
        for result in results:
            try:
                # Map result to lead data
                lead_data = map_apify_result_to_lead(result, run_data, actor_id)
                
                # Skip invalid records
                if not lead_data or not lead_data.get('email'):
                    stats['skipped'] += 1
                    continue
                
                # Check if lead already exists (by email or external_id)
                existing_lead = None
                if lead_data.get('email'):
                    existing_lead = LeadCRUD.get_by_email(session, lead_data['email'])
                
                if not existing_lead and lead_data.get('external_id'):
                    existing_lead = LeadCRUD.get_by_external_id(
                        session,
                        'apify',
                        lead_data['external_id']
                    )
                
                if existing_lead:
                    # Skip duplicate
                    stats['skipped'] += 1
                    logger.debug(f"Skipping duplicate lead: {lead_data.get('email') or lead_data.get('external_id')}")
                    continue
                
                # Create company if needed
                company_id = None
                if lead_data.get('company_domain'):
                    company = CompanyCRUD.get_or_create(
                        session=session,
                        domain=lead_data['company_domain'],
                        name=lead_data.get('company_name'),
                        industry=lead_data.get('industry'),
                        country=lead_data.get('country'),
                        city=lead_data.get('city')
                    )
                    company_id = company.id
                    lead_data['company_id'] = company_id
                
                # Create lead
                lead = LeadCRUD.create(
                    session=session,
                    **lead_data
                )
                
                # Create lead source
                LeadSourceCRUD.create(
                    session=session,
                    lead_id=lead.id,
                    source_type='apify',
                    source_name=actor_name or f'Actor {actor_id}',
                    provider_name='apify',
                    actor_id=actor_id,
                    actor_name=actor_name,
                    run_id=run_id,
                    dataset_id=run_data.get('defaultDatasetId'),
                    external_id=lead_data.get('external_id'),
                    scrape_params=scrape_params
                )
                
                stats['imported'] += 1
                
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error importing lead: {e}")
                logger.debug(f"Result data: {result}")
        
        # Update sync state
        sync_state.mark_completed(
            synced_count=stats['imported'],
            failed_count=stats['errors'],
            duplicate_count=stats['skipped']
        )
        
        session.commit()
    
    return stats


def import_from_file(filepath: str, actor_id: str, actor_name: Optional[str] = None) -> Dict[str, int]:
    """
    Import leads from a JSON file (previously scraped data)
    
    Args:
        filepath: Path to JSON file
        actor_id: Apify actor ID
        actor_name: Actor name (optional)
        
    Returns:
        Dictionary with import statistics
    """
    data_manager = DataManager()
    results = data_manager.load_json(filepath)
    
    # Create mock run_data for file imports
    run_data = {
        'id': f'file_import_{Path(filepath).stem}',
        'defaultDatasetId': None,
        'status': 'SUCCEEDED'
    }
    
    logger.info(f"Importing {len(results)} leads from {filepath}")
    stats = import_leads_to_database(
        results=results,
        run_data=run_data,
        actor_id=actor_id,
        actor_name=actor_name
    )
    
    return stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Import Apify leads into database')
    parser.add_argument('--file', help='JSON file to import')
    parser.add_argument('--actor-id', required=True, help='Apify actor ID')
    parser.add_argument('--actor-name', help='Actor name')
    
    args = parser.parse_args()
    
    load_dotenv()
    
    if args.file:
        stats = import_from_file(args.file, args.actor_id, args.actor_name)
    else:
        logger.error("Please provide --file argument")
        sys.exit(1)
    
    logger.info("\n" + "=" * 60)
    logger.info("Import Summary:")
    logger.info("=" * 60)
    logger.info(f"Total records: {stats['total']}")
    logger.info(f"Imported: {stats['imported']}")
    logger.info(f"Skipped (duplicates): {stats['skipped']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("=" * 60)

