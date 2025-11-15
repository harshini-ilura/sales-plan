#!/usr/bin/env python3
"""
CLI script for scraping leads using Apify actors
Supports both email and phone number extraction
"""
import argparse
import sys
import os
from pathlib import Path
import logging
from typing import List, Optional

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_scraper import EmailScraper
from src.phone_scraper import PhoneScraper
from src.data_manager import DataManager
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Scrape leads (emails and phone numbers) using Apify platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape emails for Chennai
  python scripts/scrape_leads_apify.py --type email --locations chennai

  # Scrape phone numbers for Dubai with industry filter
  python scripts/scrape_leads_apify.py --type phone --locations dubai --industries software technology

  # Scrape both with custom max results
  python scripts/scrape_leads_apify.py --type both --locations chennai dubai --max-results 200

  # Save to specific filename
  python scripts/scrape_leads_apify.py --type email --locations chennai --output my_leads
        """
    )

    parser.add_argument(
        '--type',
        choices=['email', 'phone', 'both'],
        required=True,
        help='Type of data to scrape'
    )

    parser.add_argument(
        '--locations',
        nargs='+',
        required=True,
        help='Organization locations to search (e.g., chennai dubai)'
    )

    parser.add_argument(
        '--industries',
        nargs='+',
        help='Industries to filter by (e.g., software technology)'
    )

    parser.add_argument(
        '--company-types',
        nargs='+',
        default=['PRIVATE'],
        help='Company types (default: PRIVATE)'
    )

    parser.add_argument(
        '--employee-min',
        type=int,
        default=0,
        help='Minimum employee count'
    )

    parser.add_argument(
        '--employee-max',
        type=int,
        help='Maximum employee count'
    )

    parser.add_argument(
        '--max-results',
        type=int,
        default=100,
        help='Maximum number of results (default: 100)'
    )

    parser.add_argument(
        '--output',
        help='Output filename (without extension)'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'both'],
        default='both',
        help='Output format (default: both)'
    )

    parser.add_argument(
        '--no-timestamp',
        action='store_true',
        help='Don\'t include timestamp in output filename'
    )

    parser.add_argument(
        '--token',
        help='Apify API token (overrides environment variable)'
    )

    return parser.parse_args()


def scrape_emails(args) -> List[dict]:
    """Scrape emails using email scraper"""
    logger.info("=" * 60)
    logger.info("Starting EMAIL scraping")
    logger.info("=" * 60)

    scraper = EmailScraper(api_token=args.token)

    try:
        run_data, results = scraper.scrape(
            organization_locations=args.locations,
            max_results=args.max_results,
            additional_params={
                'industries': args.industries,
                'employeeSizeMin': args.employee_min,
                'employeeSizeMax': args.employee_max
            } if args.industries or args.employee_max else None
        )

        # Print summary
        summary = EmailScraper.extract_email_summary(results)
        logger.info("\nEmail Scraping Summary:")
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")

        return results

    except Exception as e:
        logger.error(f"Email scraping failed: {e}")
        raise


def scrape_phones(args) -> List[dict]:
    """Scrape phone numbers using phone scraper"""
    logger.info("=" * 60)
    logger.info("Starting PHONE NUMBER scraping")
    logger.info("=" * 60)

    scraper = PhoneScraper(api_token=args.token)

    try:
        run_data, results = scraper.scrape(
            organization_locations=args.locations,
            industries=args.industries,
            company_types=args.company_types,
            employee_size_min=args.employee_min,
            employee_size_max=args.employee_max,
            max_results=args.max_results
        )

        # Print summary
        summary = PhoneScraper.extract_phone_summary(results)
        logger.info("\nPhone Scraping Summary:")
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")

        return results

    except Exception as e:
        logger.error(f"Phone scraping failed: {e}")
        raise


def main():
    """Main execution function"""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_arguments()

    # Validate API token
    api_token = args.token or os.getenv('APIFY_API_TOKEN')
    if not api_token:
        logger.error("Error: APIFY_API_TOKEN not found.")
        logger.error("Please set it in .env file or pass via --token argument")
        sys.exit(1)

    # Initialize data manager
    data_manager = DataManager()

    try:
        # Perform scraping based on type
        all_results = []

        if args.type in ['email', 'both']:
            email_results = scrape_emails(args)
            all_results.extend(email_results)

        if args.type in ['phone', 'both']:
            phone_results = scrape_phones(args)
            if args.type == 'both':
                # Merge with email results
                all_results = data_manager.merge_datasets(
                    [all_results, phone_results],
                    deduplicate_by='email' if email_results else None
                )
            else:
                all_results.extend(phone_results)

        if not all_results:
            logger.warning("No results found!")
            return

        # Determine output filename
        if args.output:
            filename = args.output
        else:
            filename = f"{args.type}_leads_{'_'.join(args.locations)}"

        # Save results
        logger.info("\n" + "=" * 60)
        logger.info("Saving results...")
        logger.info("=" * 60)

        include_timestamp = not args.no_timestamp

        if args.format == 'json':
            output_path = data_manager.save_json(
                all_results,
                filename=filename,
                include_timestamp=include_timestamp
            )
            logger.info(f"\nResults saved to: {output_path}")

        elif args.format == 'csv':
            output_path = data_manager.save_csv(
                all_results,
                filename=filename,
                include_timestamp=include_timestamp
            )
            logger.info(f"\nResults saved to: {output_path}")

        else:  # both
            output_paths = data_manager.save_both_formats(
                all_results,
                filename=filename,
                include_timestamp=include_timestamp
            )
            logger.info(f"\nResults saved to:")
            logger.info(f"  JSON: {output_paths['json']}")
            logger.info(f"  CSV:  {output_paths['csv']}")

        # Print final summary
        logger.info("\n" + "=" * 60)
        logger.info("Overall Summary:")
        logger.info("=" * 60)
        summary = data_manager.get_summary_stats(all_results)
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")

        logger.info("\n✓ Scraping completed successfully!")

    except KeyboardInterrupt:
        logger.warning("\n\nScraping interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"\n✗ Scraping failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
