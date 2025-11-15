#!/usr/bin/env python3
"""
Database management script
Handles database initialization, migrations, and testing
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import init_db, drop_db, get_session
from database.models import SalesLead, Company, LeadSource, ApifySyncState, LeadEvent
from database.crud import LeadCRUD, CompanyCRUD, LeadSourceCRUD, ApifySyncCRUD, EventCRUD


def initialize_database():
    """Initialize database - create all tables"""
    print("Initializing database...")
    try:
        init_db()
        print("✓ Database initialized successfully")
        print("  All tables created")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return False


def drop_database():
    """Drop all tables"""
    print("WARNING: This will delete all data!")
    response = input("Type 'yes' to confirm: ")

    if response.lower() != 'yes':
        print("Aborted")
        return False

    try:
        drop_db()
        print("✓ Database dropped successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to drop database: {e}")
        return False


def test_crud():
    """Test CRUD operations"""
    print("\n" + "=" * 60)
    print("Testing CRUD Operations")
    print("=" * 60)

    session = get_session()

    try:
        # Test Company CRUD
        print("\n1. Creating company...")
        company = CompanyCRUD.create(
            session=session,
            name="Test Company Inc",
            domain="testcompany.com",
            country="India",
            city="Chennai",
            industry="software",
            created_by="system"
        )
        session.commit()
        print(f"✓ Company created: ID={company.id}, Name={company.name}")

        # Test Lead CRUD
        print("\n2. Creating lead...")
        lead = LeadCRUD.create(
            session=session,
            full_name="John Doe",
            email="john.doe@testcompany.com",
            phone="+91-1234567890",
            company_id=company.id,
            company_name=company.name,
            company_domain=company.domain,
            country="India",
            city="Chennai",
            source="apify",
            provider_name="apify",
            actor_id="T1XDXWc1L92AfIJtd",
            run_id="test_run_123",
            created_by="system"
        )
        session.commit()
        print(f"✓ Lead created: ID={lead.id}, Name={lead.full_name}, Email={lead.email}")

        # Test Lead Source CRUD
        print("\n3. Creating lead source...")
        source = LeadSourceCRUD.create(
            session=session,
            lead_id=lead.id,
            source_type="apify",
            source_name="Apify Email Scraper",
            provider_name="apify",
            actor_id="T1XDXWc1L92AfIJtd",
            run_id="test_run_123",
            created_by="system"
        )
        session.commit()
        print(f"✓ Lead source created: ID={source.id}")

        # Test Apify Sync State CRUD
        print("\n4. Creating sync state...")
        sync_state = ApifySyncCRUD.create(
            session=session,
            actor_id="T1XDXWc1L92AfIJtd",
            actor_name="Email Scraper",
            run_id="test_run_123",
            sync_status="completed",
            total_records=1,
            synced_records=1,
            created_by="system"
        )
        session.commit()
        print(f"✓ Sync state created: ID={sync_state.id}, Run ID={sync_state.run_id}")

        # Test Read operations
        print("\n5. Testing read operations...")
        lead_by_id = LeadCRUD.get_by_id(session, lead.id)
        print(f"✓ Get by ID: {lead_by_id.full_name}")

        lead_by_email = LeadCRUD.get_by_email(session, "john.doe@testcompany.com")
        print(f"✓ Get by email: {lead_by_email.full_name}")

        # Test Update operations
        print("\n6. Testing update operations...")
        updated_lead = LeadCRUD.update(
            session,
            lead.id,
            lead_status="contacted",
            updated_by="system"
        )
        session.commit()
        print(f"✓ Lead updated: Status={updated_lead.lead_status}")

        # Test Events
        print("\n7. Testing events...")
        events = EventCRUD.get_lead_events(session, lead.id)
        print(f"✓ Lead has {len(events)} events")
        for event in events:
            print(f"  - {event.event_type}: {event.event_name}")

        # Test Soft Delete
        print("\n8. Testing soft delete...")
        LeadCRUD.delete(session, lead.id, deleted_by="system")
        session.commit()
        deleted_lead = LeadCRUD.get_by_id(session, lead.id, include_deleted=True)
        print(f"✓ Lead soft deleted: is_deleted={deleted_lead.is_deleted}")

        # Test Restore
        print("\n9. Testing restore...")
        restored_lead = LeadCRUD.restore(session, lead.id)
        session.commit()
        print(f"✓ Lead restored: is_deleted={restored_lead.is_deleted}")

        # Test List operations
        print("\n10. Testing list operations...")
        leads = LeadCRUD.list_leads(session, limit=10)
        print(f"✓ Listed {len(leads)} leads")

        count = LeadCRUD.count(session)
        print(f"✓ Total leads: {count}")

        print("\n" + "=" * 60)
        print("✓ All CRUD tests passed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ CRUD test failed: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False
    finally:
        session.close()

    return True


def show_schema():
    """Show database schema information"""
    print("\n" + "=" * 60)
    print("Database Schema")
    print("=" * 60)

    from database.models import Base

    tables = Base.metadata.tables

    for table_name, table in tables.items():
        print(f"\nTable: {table_name}")
        print(f"  Columns ({len(table.columns)}):")
        for column in table.columns:
            nullable = "NULL" if column.nullable else "NOT NULL"
            pk = " PRIMARY KEY" if column.primary_key else ""
            fk = " FOREIGN KEY" if column.foreign_keys else ""
            print(f"    - {column.name}: {column.type} {nullable}{pk}{fk}")

        if table.indexes:
            print(f"  Indexes ({len(table.indexes)}):")
            for index in table.indexes:
                cols = ", ".join([c.name for c in index.columns])
                print(f"    - {index.name}: ({cols})")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Database management tool')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Init command
    subparsers.add_parser('init', help='Initialize database (create tables)')

    # Drop command
    subparsers.add_parser('drop', help='Drop all tables')

    # Test command
    subparsers.add_parser('test', help='Test CRUD operations')

    # Schema command
    subparsers.add_parser('schema', help='Show database schema')

    # Reset command
    subparsers.add_parser('reset', help='Drop and recreate database')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'init':
        initialize_database()

    elif args.command == 'drop':
        drop_database()

    elif args.command == 'test':
        test_crud()

    elif args.command == 'schema':
        show_schema()

    elif args.command == 'reset':
        if drop_database():
            initialize_database()
            print("\n✓ Database reset complete")


if __name__ == '__main__':
    main()
