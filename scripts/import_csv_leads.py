#!/usr/bin/env python3
"""
Import leads from CSV file
"""
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_session
from database.crud import LeadCRUD, LeadSourceCRUD, CompanyCRUD
from database.models.lead_sources import LeadSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_name(full_name: str) -> tuple:
    """Split full name into first and last name"""
    if not full_name:
        return '', ''
    
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ''
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        # First name is first part, last name is everything else
        return parts[0], ' '.join(parts[1:])


def map_csv_row_to_lead(row: Dict[str, Any], source_name: str = 'import') -> Dict[str, Any]:
    """
    Map CSV row to lead data
    
    Supports common CSV column names:
    - name, full_name, first_name, last_name
    - email, email_address
    - phone, phone_number, telephone
    - company, company_name, organization
    - domain, website, company_domain
    - city, location
    - country
    - industry
    - title, position, job_title
    """
    # Normalize column names (case-insensitive, handle spaces/underscores)
    # Handle None keys (can happen with malformed CSV)
    row_lower = {}
    for k, v in row.items():
        if k is None:
            continue  # Skip None keys
        if v is None or (isinstance(v, str) and not v.strip()):
            continue  # Skip empty values
        try:
            # Normalize key: lowercase, strip, replace spaces/underscores
            key_normalized = k.lower().strip().replace(' ', '_').replace('-', '_')
            row_lower[key_normalized] = v.strip() if isinstance(v, str) else v
            # Also store original format for lookup
            row_lower[k.lower().strip()] = v.strip() if isinstance(v, str) else v
        except AttributeError:
            # If k is not a string, skip it
            continue
    
    # Extract name - try multiple variations
    full_name = (row_lower.get('full_name') or row_lower.get('name') or 
                 row_lower.get('contact_name') or '')
    first_name = (row_lower.get('first_name') or row_lower.get('firstname') or 
                  row_lower.get('first name') or '')
    last_name = (row_lower.get('last_name') or row_lower.get('lastname') or 
                 row_lower.get('last name') or '')
    
    if not first_name and not last_name and full_name:
        first_name, last_name = normalize_name(full_name)
    elif not full_name and (first_name or last_name):
        full_name = f"{first_name or ''} {last_name or ''}".strip()
    
    # Extract email
    email = (row_lower.get('email') or row_lower.get('email_address') or 
             row_lower.get('e-mail') or '').strip()
    
    if not email:
        return None  # Skip rows without email
    
    # Extract phone - try multiple phone fields
    phone = (row_lower.get('phone') or row_lower.get('phone_number') or 
             row_lower.get('telephone') or row_lower.get('mobile') or 
             row_lower.get('work_direct_phone') or row_lower.get('corporate_phone') or 
             row_lower.get('mobile_phone') or '').strip()
    
    # Clean up phone number (remove quotes, extra spaces)
    if phone:
        phone = phone.strip("'\"")  # Remove surrounding quotes
        phone = phone.strip()
    
    # Extract company info - try multiple variations
    company_name = (row_lower.get('company_name') or row_lower.get('company name') or
                    row_lower.get('company') or row_lower.get('organization') or 
                    row_lower.get('organization_name') or row_lower.get('organization name') or '').strip()
    
    company_domain = (row_lower.get('domain') or row_lower.get('website') or 
                     row_lower.get('company_domain') or row_lower.get('company domain') or
                     row_lower.get('company_website') or row_lower.get('company website') or '').strip()
    
    # Clean up domain
    if company_domain:
        company_domain = company_domain.replace('https://', '').replace('http://', '').replace('www.', '')
        company_domain = company_domain.rstrip('/')
        if '/' in company_domain:
            company_domain = company_domain.split('/')[0]
    
    # Extract location - try multiple variations
    city = (row_lower.get('city') or row_lower.get('location') or 
            row_lower.get('company_city') or row_lower.get('company city') or '').strip()
    country = (row_lower.get('country') or row_lower.get('company_country') or 
               row_lower.get('company country') or '').strip()
    state = (row_lower.get('state') or row_lower.get('province') or 
             row_lower.get('company_state') or row_lower.get('company state') or '').strip()
    
    # Extract industry
    industry = (row_lower.get('industry') or row_lower.get('sector') or '').strip()
    
    # Extract title - try multiple variations
    title = (row_lower.get('title') or row_lower.get('position') or 
             row_lower.get('job_title') or row_lower.get('job title') or
             row_lower.get('role') or '').strip()
    
    # Use email as external_id for CSV imports
    external_id = email
    
    lead_data = {
        'full_name': full_name or None,
        'first_name': first_name or None,
        'last_name': last_name or None,
        'title': title or None,
        'email': email,
        'phone': phone or None,
        'company_name': company_name or None,
        'company_domain': company_domain or None,
        'country': country or None,
        'city': city or None,
        'state': state or None,
        'industry': industry or None,
        'source': source_name,
        'provider_name': 'manual',
        'external_id': external_id,
        'raw_data': row
    }
    
    return lead_data


def import_csv_to_database(
    filepath: str,
    source_name: str = 'CSV Import',
    skip_duplicates: bool = True
) -> Dict[str, int]:
    """
    Import leads from CSV file
    
    Args:
        filepath: Path to CSV file
        source_name: Name for the import source
        skip_duplicates: Skip leads that already exist
        
    Returns:
        Dictionary with import statistics
    """
    stats = {
        'total': 0,
        'imported': 0,
        'skipped': 0,
        'errors': 0
    }
    
    session = None
    try:
        session = get_session()
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            
            # Try common delimiters - prioritize comma
            # Count potential delimiters in first few lines
            first_lines = sample.split('\n')[:3]
            comma_count = sum(line.count(',') for line in first_lines if line.strip())
            semicolon_count = sum(line.count(';') for line in first_lines if line.strip())
            tab_count = sum(line.count('\t') for line in first_lines if line.strip())
            
            # Choose delimiter based on counts - be strict
            # For CSV files, comma should be most common
            if comma_count > 0:
                # If comma is present, prefer it unless semicolon/tab is clearly dominant
                if tab_count > comma_count * 2:  # Tab needs to be 2x more common
                    delimiter = '\t'
                elif semicolon_count > comma_count * 2:  # Semicolon needs to be 2x more common
                    delimiter = ';'
                else:
                    delimiter = ','  # Default to comma
            elif semicolon_count > tab_count:
                delimiter = ';'
            elif tab_count > 0:
                delimiter = '\t'
            else:
                # Fallback: try sniffer but only accept standard delimiters
                delimiter = ','
                try:
                    sniffer = csv.Sniffer()
                    detected = sniffer.sniff(sample, delimiters=',;\t')
                    # Only use if it's one of our accepted delimiters
                    if detected.delimiter in [',', ';', '\t']:
                        delimiter = detected.delimiter
                except:
                    delimiter = ','  # Default to comma
            
            logger.info(f"Using delimiter: '{delimiter}'")
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Check if we have headers
            if not reader.fieldnames:
                raise ValueError("CSV file appears to be empty or has no headers")
            
            logger.info(f"CSV columns detected: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                stats['total'] += 1
                
                # Skip completely empty rows
                if not any(v and str(v).strip() for v in row.values()):
                    stats['skipped'] += 1
                    logger.debug(f"Row {row_num}: Skipped (empty row)")
                    continue
                
                try:
                    # Map CSV row to lead data
                    lead_data = map_csv_row_to_lead(row, source_name)
                    
                    if not lead_data or not lead_data.get('email'):
                        stats['skipped'] += 1
                        logger.warning(f"Row {row_num}: Skipped (no email). Row keys: {list(row.keys())}")
                        continue
                    
                    # Check for duplicates
                    if skip_duplicates:
                        existing_lead = LeadCRUD.get_by_email(session, lead_data['email'])
                        if existing_lead:
                            stats['skipped'] += 1
                            logger.debug(f"Row {row_num}: Skipped duplicate - {lead_data['email']}")
                            continue
                    
                    # Create company if needed
                    company_id = None
                    if lead_data.get('company_domain'):
                        try:
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
                        except Exception as e:
                            logger.warning(f"Row {row_num}: Error creating company - {e}. Continuing without company.")
                    
                    # Remove raw_data if it can't be serialized
                    if 'raw_data' in lead_data:
                        try:
                            import json
                            json.dumps(lead_data['raw_data'])
                        except:
                            logger.warning(f"Row {row_num}: raw_data not JSON serializable, removing it")
                            lead_data.pop('raw_data', None)
                    
                    # Create lead
                    lead = LeadCRUD.create(
                        session=session,
                        **lead_data
                    )
                    
                    # Create lead source (check if it already exists)
                    try:
                        existing_source = session.query(LeadSource).filter(
                            LeadSource.lead_id == lead.id
                        ).first()
                        
                        if not existing_source:
                            LeadSourceCRUD.create(
                                session=session,
                                lead_id=lead.id,
                                source_type='import',
                                source_name=source_name,
                                provider_name='manual',
                                external_id=lead_data.get('external_id'),
                                import_batch_id=f'csv_import_{Path(filepath).stem}'
                            )
                    except Exception as e:
                        logger.warning(f"Row {row_num}: Error creating lead source - {e}. Lead created but source not tracked.")
                    
                    stats['imported'] += 1
                    logger.debug(f"Row {row_num}: Successfully imported {lead_data['email']}")
                    
                except Exception as e:
                    stats['errors'] += 1
                    session.rollback()
                    import traceback
                    error_msg = f"Row {row_num}: Error importing lead - {e}"
                    logger.error(error_msg)
                    logger.error(f"Row data: {row}")
                    logger.error(f"Full traceback:\n{traceback.format_exc()}")
                    # Print to console for web UI visibility
                    print(f"ERROR Row {row_num}: {e}")
                    print(f"Row data: {row}")
        
        session.commit()
        logger.info(f"Committed {stats['imported']} leads to database")
        
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Fatal error during import: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        if session:
            session.close()
    
    return stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Import leads from CSV file')
    parser.add_argument('file', help='CSV file to import')
    parser.add_argument('--source-name', default='CSV Import', help='Source name')
    parser.add_argument('--no-skip-duplicates', action='store_true', help='Import duplicates too')
    
    args = parser.parse_args()
    
    stats = import_csv_to_database(
        filepath=args.file,
        source_name=args.source_name,
        skip_duplicates=not args.no_skip_duplicates
    )
    
    logger.info("\n" + "=" * 60)
    logger.info("Import Summary:")
    logger.info("=" * 60)
    logger.info(f"Total rows: {stats['total']}")
    logger.info(f"Imported: {stats['imported']}")
    logger.info(f"Skipped (duplicates): {stats['skipped']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("=" * 60)
