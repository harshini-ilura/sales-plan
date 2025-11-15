"""
Apify API Client for actor execution and data retrieval
"""
import os
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApifyClient:
    """Client for interacting with Apify API"""

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Apify client

        Args:
            api_token: Apify API token. If not provided, reads from APIFY_API_TOKEN env var
        """
        self.api_token = api_token or os.getenv('APIFY_API_TOKEN')
        if not self.api_token:
            raise ValueError(
                "Apify API token not found. Please set APIFY_API_TOKEN environment variable "
                "or pass it to the constructor."
            )

        self.base_url = "https://api.apify.com/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def run_actor(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        timeout: int = 3600,
        memory_mbytes: int = 256
    ) -> Dict[str, Any]:
        """
        Start an actor run

        Args:
            actor_id: The actor ID to run
            input_data: Input parameters for the actor
            timeout: Maximum runtime in seconds
            memory_mbytes: Memory allocation for the actor

        Returns:
            Run information including run ID and dataset ID
        """
        url = f"{self.base_url}/acts/{actor_id}/runs"
        params = {'token': self.api_token}

        logger.info(f"Starting actor {actor_id}...")
        logger.debug(f"Input data: {input_data}")

        try:
            response = self.session.post(
                url,
                json=input_data,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            run_data = result.get('data', {})

            logger.info(f"Actor started successfully. Run ID: {run_data.get('id')}")
            logger.info(f"Dataset ID: {run_data.get('defaultDatasetId')}")
            logger.info(f"Status: {run_data.get('status')}")

            return run_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start actor: {e}")
            raise

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the status of an actor run

        Args:
            run_id: The run ID to check

        Returns:
            Run status information
        """
        url = f"{self.base_url}/actor-runs/{run_id}"
        params = {'token': self.api_token}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get('data', {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get run status: {e}")
            raise

    def wait_for_completion(
        self,
        run_id: str,
        poll_interval: int = 5,
        max_wait_time: int = 3600
    ) -> Dict[str, Any]:
        """
        Wait for an actor run to complete

        Args:
            run_id: The run ID to wait for
            poll_interval: Seconds between status checks
            max_wait_time: Maximum time to wait in seconds

        Returns:
            Final run status
        """
        logger.info(f"Waiting for run {run_id} to complete...")
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise TimeoutError(f"Run did not complete within {max_wait_time} seconds")

            status_data = self.get_run_status(run_id)
            status = status_data.get('status')

            logger.info(f"Current status: {status} (elapsed: {int(elapsed)}s)")

            if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
                if status == 'SUCCEEDED':
                    logger.info(f"Run completed successfully!")
                    finished_at = status_data.get('finishedAt')
                    started_at = status_data.get('startedAt')
                    if finished_at and started_at:
                        logger.info(f"Run duration: {finished_at} - {started_at}")
                else:
                    logger.error(f"Run finished with status: {status}")

                return status_data

            time.sleep(poll_interval)

    def get_dataset_items(
        self,
        dataset_id: str,
        format: str = 'json',
        clean: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve items from a dataset

        Args:
            dataset_id: The dataset ID
            format: Output format (json, csv, etc.)
            clean: Whether to return clean items only

        Returns:
            List of dataset items
        """
        url = f"{self.base_url}/datasets/{dataset_id}/items"
        params = {
            'token': self.api_token,
            'format': format
        }

        if clean:
            params['clean'] = 'true'

        logger.info(f"Fetching dataset items from {dataset_id}...")

        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()

            if format == 'json':
                items = response.json()
                logger.info(f"Retrieved {len(items)} items from dataset")
                return items
            else:
                # For CSV or other formats, return raw content
                logger.info(f"Retrieved dataset in {format} format")
                return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get dataset items: {e}")
            raise

    def run_and_wait(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        poll_interval: int = 5,
        max_wait_time: int = 3600
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Run an actor and wait for completion, then return the results

        Args:
            actor_id: The actor ID to run
            input_data: Input parameters for the actor
            poll_interval: Seconds between status checks
            max_wait_time: Maximum time to wait in seconds

        Returns:
            Tuple of (run_data, dataset_items)
        """
        # Start the run
        run_data = self.run_actor(actor_id, input_data)
        run_id = run_data.get('id')
        dataset_id = run_data.get('defaultDatasetId')

        # Wait for completion
        final_status = self.wait_for_completion(
            run_id,
            poll_interval=poll_interval,
            max_wait_time=max_wait_time
        )

        # Get results if successful
        if final_status.get('status') == 'SUCCEEDED':
            items = self.get_dataset_items(dataset_id)
            return final_status, items
        else:
            raise RuntimeError(
                f"Actor run failed with status: {final_status.get('status')}"
            )

    def get_actor_info(self, actor_id: str) -> Dict[str, Any]:
        """
        Get information about an actor

        Args:
            actor_id: The actor ID

        Returns:
            Actor information
        """
        url = f"{self.base_url}/acts/{actor_id}"
        params = {'token': self.api_token}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get('data', {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get actor info: {e}")
            raise
