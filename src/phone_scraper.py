"""
Phone scraper using Apify actor aihL2lJmGDt9XFCGg
Extracts phone numbers and company information
"""
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .apify_client import ApifyClient

logger = logging.getLogger(__name__)


class PhoneScraper:
    """Scraper for extracting phone numbers and company data using Apify"""

    # Actor ID for phone number extraction
    ACTOR_ID = "aihL2lJmGDt9XFCGg"

    def __init__(self, api_token: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize phone scraper

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

        self.actor_config = self.config['actors']['phone_scraper']
        self.api_config = self.config['api']

    def scrape(
        self,
        organization_locations: List[str],
        industries: Optional[List[str]] = None,
        company_types: Optional[List[str]] = None,
        employee_size_min: int = 0,
        employee_size_max: Optional[int] = None,
        max_results: int = 100,
        get_emails: bool = True,
        include_risky_emails: bool = True,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Scrape phone numbers and company information

        Args:
            organization_locations: List of location names (e.g., ["dubai", "chennai"])
            industries: List of industry names (e.g., ["software", "technology"])
            company_types: List of company types (e.g., ["PRIVATE", "PUBLIC"])
            employee_size_min: Minimum employee count
            employee_size_max: Maximum employee count (optional)
            max_results: Maximum number of results to return
            get_emails: Whether to also extract emails
            include_risky_emails: Whether to include risky/unverified emails
            additional_params: Additional parameters to pass to the actor

        Returns:
            Tuple of (run_data, results)
        """
        # Build input parameters with defaults
        input_data = {
            "companyTypes": company_types or ["PRIVATE"],
            "employeeSizeMin": employee_size_min,
            "getEmails": get_emails,
            "includeRiskyEmails": include_risky_emails,
            "maxResults": max_results,
            "organizationLocations": organization_locations
        }

        # Add optional parameters
        if industries:
            input_data["industries"] = industries

        if employee_size_max is not None:
            input_data["employeeSizeMax"] = employee_size_max

        # Merge with additional parameters if provided
        if additional_params:
            input_data.update(additional_params)

        logger.info(f"Starting phone scraper for locations: {organization_locations}")
        if industries:
            logger.info(f"Industries: {industries}")
        logger.info(f"Max results: {max_results}")

        # Run the actor and wait for completion
        run_data, results = self.client.run_and_wait(
            actor_id=self.ACTOR_ID,
            input_data=input_data,
            poll_interval=self.api_config['poll_interval'],
            max_wait_time=self.api_config['timeout']
        )

        logger.info(f"Phone scraping completed. Retrieved {len(results)} records")

        return run_data, results

    def scrape_by_industry(
        self,
        industries: List[str],
        organization_locations: List[str],
        max_results: int = 100,
        **kwargs
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Scrape phone numbers filtered by specific industries

        Args:
            industries: List of industry names
            organization_locations: List of location names
            max_results: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Tuple of (run_data, results)
        """
        return self.scrape(
            organization_locations=organization_locations,
            industries=industries,
            max_results=max_results,
            **kwargs
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
        Scrape phone numbers filtered by company size

        Args:
            organization_locations: List of location names
            employee_size_min: Minimum employee count
            employee_size_max: Maximum employee count (optional)
            max_results: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Tuple of (run_data, results)
        """
        return self.scrape(
            organization_locations=organization_locations,
            employee_size_min=employee_size_min,
            employee_size_max=employee_size_max,
            max_results=max_results,
            **kwargs
        )

    def scrape_tech_companies(
        self,
        organization_locations: List[str],
        max_results: int = 100,
        **kwargs
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Convenience method to scrape tech companies

        Args:
            organization_locations: List of location names
            max_results: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Tuple of (run_data, results)
        """
        return self.scrape(
            organization_locations=organization_locations,
            industries=["software", "technology", "IT Services"],
            max_results=max_results,
            **kwargs
        )

    @staticmethod
    def extract_phone_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract summary statistics from phone scraping results

        Args:
            results: List of result records

        Returns:
            Dictionary with summary statistics
        """
        total_records = len(results)
        phones_found = 0
        emails_found = 0
        companies = set()
        locations = set()
        industries = set()

        for record in results:
            if record.get('phone') or record.get('phoneNumber'):
                phones_found += 1
            if record.get('email'):
                emails_found += 1
            if record.get('companyName'):
                companies.add(record.get('companyName'))
            if record.get('location'):
                locations.add(record.get('location'))
            if record.get('industry'):
                industries.add(record.get('industry'))

        return {
            "total_records": total_records,
            "phones_found": phones_found,
            "emails_found": emails_found,
            "unique_companies": len(companies),
            "unique_locations": len(locations),
            "unique_industries": len(industries),
            "phone_rate": f"{(phones_found/total_records*100):.1f}%" if total_records > 0 else "0%",
            "email_rate": f"{(emails_found/total_records*100):.1f}%" if total_records > 0 else "0%"
        }
