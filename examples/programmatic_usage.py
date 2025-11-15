#!/usr/bin/env python3
"""
Example: Programmatic usage of the Apify lead scrapers
Demonstrates how to use the scrapers directly in Python code
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_scraper import EmailScraper
from src.phone_scraper import PhoneScraper
from src.data_manager import DataManager
from dotenv import load_dotenv


def example_email_scraping():
    """Example: Scrape emails from Chennai"""
    print("=" * 60)
    print("Example 1: Email Scraping")
    print("=" * 60)

    # Initialize scraper
    scraper = EmailScraper()

    # Scrape emails
    run_data, results = scraper.scrape(
        organization_locations=["chennai"],
        max_results=50
    )

    # Get summary
    summary = EmailScraper.extract_email_summary(results)
    print(f"\nResults: {summary['total_records']} records")
    print(f"Emails found: {summary['emails_found']}")
    print(f"Companies: {summary['unique_companies']}")

    return results


def example_phone_scraping():
    """Example: Scrape phone numbers from Dubai tech companies"""
    print("\n" + "=" * 60)
    print("Example 2: Phone Number Scraping")
    print("=" * 60)

    # Initialize scraper
    scraper = PhoneScraper()

    # Scrape phone numbers for tech companies
    run_data, results = scraper.scrape_tech_companies(
        organization_locations=["dubai"],
        max_results=50
    )

    # Get summary
    summary = PhoneScraper.extract_phone_summary(results)
    print(f"\nResults: {summary['total_records']} records")
    print(f"Phones found: {summary['phones_found']}")
    print(f"Emails found: {summary['emails_found']}")
    print(f"Companies: {summary['unique_companies']}")

    return results


def example_filtered_scraping():
    """Example: Scrape with specific filters"""
    print("\n" + "=" * 60)
    print("Example 3: Filtered Scraping")
    print("=" * 60)

    scraper = PhoneScraper()

    # Scrape with multiple filters
    run_data, results = scraper.scrape(
        organization_locations=["chennai", "bangalore"],
        industries=["software", "technology"],
        employee_size_min=10,
        employee_size_max=200,
        max_results=30
    )

    print(f"\nRetrieved {len(results)} results")

    return results


def example_data_management():
    """Example: Data management and export"""
    print("\n" + "=" * 60)
    print("Example 4: Data Management")
    print("=" * 60)

    # Initialize data manager
    dm = DataManager()

    # Create sample data
    data = [
        {"email": "test1@example.com", "company": "Company A"},
        {"email": "test2@example.com", "company": "Company B"},
        {"email": "test3@example.com", "company": "Company C"},
    ]

    # Save in both formats
    paths = dm.save_both_formats(data, filename="example_leads")

    print(f"\nData saved to:")
    print(f"  JSON: {paths['json']}")
    print(f"  CSV:  {paths['csv']}")

    # Get summary stats
    stats = dm.get_summary_stats(data)
    print(f"\nSummary: {stats}")

    return paths


def example_merge_datasets():
    """Example: Merge multiple datasets"""
    print("\n" + "=" * 60)
    print("Example 5: Merging Datasets")
    print("=" * 60)

    dm = DataManager()

    # Sample datasets
    dataset1 = [
        {"email": "user1@company.com", "name": "User 1"},
        {"email": "user2@company.com", "name": "User 2"},
    ]

    dataset2 = [
        {"email": "user2@company.com", "name": "User 2"},  # Duplicate
        {"email": "user3@company.com", "name": "User 3"},
    ]

    # Merge with deduplication
    merged = dm.merge_datasets(
        [dataset1, dataset2],
        deduplicate_by="email"
    )

    print(f"\nDataset 1: {len(dataset1)} records")
    print(f"Dataset 2: {len(dataset2)} records")
    print(f"Merged: {len(merged)} records (after deduplication)")

    return merged


def main():
    """Run all examples"""
    # Load environment variables
    load_dotenv()

    print("\n")
    print("*" * 60)
    print("Apify Lead Scraper - Programmatic Usage Examples")
    print("*" * 60)
    print("\nNOTE: These examples will make real API calls.")
    print("Press Ctrl+C to cancel.\n")

    try:
        # Example 1: Email scraping
        # email_results = example_email_scraping()

        # Example 2: Phone scraping
        # phone_results = example_phone_scraping()

        # Example 3: Filtered scraping
        # filtered_results = example_filtered_scraping()

        # Example 4: Data management (no API calls)
        paths = example_data_management()

        # Example 5: Merging datasets (no API calls)
        merged = example_merge_datasets()

        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print("=" * 60)

        print("\nTo run the scraping examples, uncomment the lines in main()")

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
