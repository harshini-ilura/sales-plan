"""
Data storage and export functionality for scraped lead data
"""
import json
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataManager:
    """Manager for storing and exporting scraped data"""

    def __init__(self, output_directory: str = "data/exports"):
        """
        Initialize data manager

        Args:
            output_directory: Directory to store exported files
        """
        self.output_dir = Path(output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_json(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        include_timestamp: bool = True
    ) -> Path:
        """
        Save data to JSON file

        Args:
            data: List of records to save
            filename: Output filename (without extension)
            include_timestamp: Whether to include timestamp in filename

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = "scraped_data"

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}"

        output_path = self.output_dir / f"{filename}.json"

        logger.info(f"Saving {len(data)} records to {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Data saved successfully to {output_path}")
        return output_path

    def save_csv(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        include_timestamp: bool = True,
        fieldnames: Optional[List[str]] = None
    ) -> Path:
        """
        Save data to CSV file

        Args:
            data: List of records to save
            filename: Output filename (without extension)
            include_timestamp: Whether to include timestamp in filename
            fieldnames: List of field names to include (if None, uses all keys from first record)

        Returns:
            Path to saved file
        """
        if not data:
            raise ValueError("Cannot save empty data to CSV")

        if filename is None:
            filename = "scraped_data"

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}"

        output_path = self.output_dir / f"{filename}.csv"

        # Determine fieldnames
        if fieldnames is None:
            # Collect all unique keys from all records
            all_keys = set()
            for record in data:
                all_keys.update(record.keys())
            fieldnames = sorted(list(all_keys))

        logger.info(f"Saving {len(data)} records to {output_path}")
        logger.info(f"CSV columns: {fieldnames}")

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Data saved successfully to {output_path}")
        return output_path

    def save_both_formats(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        include_timestamp: bool = True
    ) -> Dict[str, Path]:
        """
        Save data in both JSON and CSV formats

        Args:
            data: List of records to save
            filename: Output filename (without extension)
            include_timestamp: Whether to include timestamp in filename

        Returns:
            Dictionary with paths for both formats
        """
        json_path = self.save_json(data, filename, include_timestamp)
        csv_path = self.save_csv(data, filename, include_timestamp)

        return {
            "json": json_path,
            "csv": csv_path
        }

    def load_json(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Load data from JSON file

        Args:
            filepath: Path to JSON file

        Returns:
            List of records
        """
        path = Path(filepath)
        logger.info(f"Loading data from {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data)} records")
        return data

    def merge_datasets(
        self,
        datasets: List[List[Dict[str, Any]]],
        deduplicate_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple datasets into one

        Args:
            datasets: List of datasets to merge
            deduplicate_by: Field to use for deduplication (e.g., 'email')

        Returns:
            Merged dataset
        """
        merged = []
        seen = set()

        for dataset in datasets:
            for record in dataset:
                if deduplicate_by:
                    key = record.get(deduplicate_by)
                    if key and key in seen:
                        continue
                    if key:
                        seen.add(key)

                merged.append(record)

        logger.info(f"Merged {len(datasets)} datasets into {len(merged)} records")
        if deduplicate_by:
            logger.info(f"Deduplicated by '{deduplicate_by}'")

        return merged

    def filter_records(
        self,
        data: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter records based on criteria

        Args:
            data: List of records
            filters: Dictionary of field -> value filters

        Returns:
            Filtered records
        """
        filtered = []

        for record in data:
            match = True
            for field, value in filters.items():
                if isinstance(value, list):
                    # Check if record value is in the list
                    if record.get(field) not in value:
                        match = False
                        break
                else:
                    # Exact match
                    if record.get(field) != value:
                        match = False
                        break

            if match:
                filtered.append(record)

        logger.info(f"Filtered {len(data)} records down to {len(filtered)} records")
        return filtered

    def get_summary_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for a dataset

        Args:
            data: List of records

        Returns:
            Dictionary with summary statistics
        """
        if not data:
            return {"total_records": 0}

        total = len(data)

        # Count non-empty values for common fields
        fields_to_check = ['email', 'phone', 'phoneNumber', 'companyName', 'location', 'industry']
        field_counts = {}

        for field in fields_to_check:
            count = sum(1 for record in data if record.get(field))
            if count > 0:
                field_counts[f"{field}_count"] = count
                field_counts[f"{field}_rate"] = f"{(count/total*100):.1f}%"

        # Count unique values for certain fields
        unique_fields = ['companyName', 'location', 'industry']
        for field in unique_fields:
            unique_values = set(record.get(field) for record in data if record.get(field))
            if unique_values:
                field_counts[f"unique_{field}"] = len(unique_values)

        return {
            "total_records": total,
            **field_counts
        }

    def list_exports(self, pattern: str = "*") -> List[Path]:
        """
        List all exported files

        Args:
            pattern: Glob pattern to filter files

        Returns:
            List of file paths
        """
        files = sorted(self.output_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        return files
