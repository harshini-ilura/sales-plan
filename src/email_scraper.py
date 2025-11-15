"""
Email scraper using Apify actor T1XDXWc1L92AfIJtd
Extracts verified emails from organizations
"""
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .apify_client import ApifyClient

logger = logging.getLogger(__name__)


class EmailScraper:
    """Scraper for extracting verified emails using Apify"""

    # Actor ID for verified email extraction
    ACTOR_ID = "T1XDXWc1L92AfIJtd"

    def __init__(self, api_token: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize email scraper

        Args:
            api_token: Apify API token
            config_path: Path to config.yaml file
        """
        self.client = ApifyClient(api_token)

        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.actor_config = self.config['actors']['email_scraper']
        self.api_config = self.config['api']

    def scrape(
        self,
        organization_locations: List[str],
        max_results: int = 100,
        get_emails: bool = True,
        include_risky_emails: bool = True,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Scrape verified emails from organizations

        Args:
            organization_locations: List of location names (e.g., ["chennai", "dubai"])
            max_results: Maximum number of results to return
            get_emails: Whether to extract emails
            include_risky_emails: Whether to include risky/unverified emails
            additional_params: Additional parameters to pass to the actor

        Returns:
            Tuple of (run_data, results)
        """
        # Build input parameters
        input_data = {
            "getEmails": get_emails,
            "includeRiskyEmails": include_risky_emails,
            "maxResults": max_results,
            "organizationLocations": organization_locations
        }

        # Merge with additional parameters if provided
        if additional_params:
            input_data.update(additional_params)

        logger.info(f"Starting email scraper for locations: {organization_locations}")
        logger.info(f"Max results: {max_results}")

        # Run the actor and wait for completion
        run_data, results = self.client.run_and_wait(
            actor_id=self.ACTOR_ID,
            input_data=input_data,
            poll_interval=self.api_config['poll_interval'],
            max_wait_time=self.api_config['timeout']
        )

        logger.info(f"Email scraping completed. Retrieved {len(results)} records")

        return run_data, results

    def scrape_by_industry(
        self,
        industries: List[str],
        organization_locations: List[str],
        max_results: int = 100,
        **kwargs
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Scrape emails filtered by industries

        Args:
            industries: List of industry names
            organization_locations: List of location names
            max_results: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Tuple of (run_data, results)
        """
        additional_params = {
            "industries": industries,
            **kwargs
        }

        return self.scrape(
            organization_locations=organization_locations,
            max_results=max_results,
            additional_params=additional_params
        )

    def scrape_by_company_size(
        self,
        organization_locations: List[str],
        employee_size_min: int = 0,
        employee_size_max: Optional[int] = None,
        max_results: int = 100,
        **kwargs
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Scrape emails filtered by company size

        Args:
            organization_locations: List of location names
            employee_size_min: Minimum employee count
            employee_size_max: Maximum employee count (optional)
            max_results: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Tuple of (run_data, results)
        """
        additional_params = {
            "employeeSizeMin": employee_size_min,
            **kwargs
        }

        if employee_size_max is not None:
            additional_params["employeeSizeMax"] = employee_size_max

        return self.scrape(
            organization_locations=organization_locations,
            max_results=max_results,
            additional_params=additional_params
        )

    @staticmethod
    def extract_email_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract summary statistics from email scraping results

        Args:
            results: List of result records

        Returns:
            Dictionary with summary statistics
        """
        total_records = len(results)
        emails_found = 0
        companies = set()
        locations = set()

        for record in results:
            if record.get('email'):
                emails_found += 1
            if record.get('companyName'):
                companies.add(record.get('companyName'))
            if record.get('location'):
                locations.add(record.get('location'))

        return {
            "total_records": total_records,
            "emails_found": emails_found,
            "unique_companies": len(companies),
            "unique_locations": len(locations),
            "email_rate": f"{(emails_found/total_records*100):.1f}%" if total_records > 0 else "0%"
        }
