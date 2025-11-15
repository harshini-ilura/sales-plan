#!/usr/bin/env python3
"""
Utility script to merge multiple exported data files
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_manager import DataManager


def merge_files(file_paths, output_name, deduplicate_by=None):
    """Merge multiple JSON files"""
    dm = DataManager()

    print("=" * 60)
    print("Merging Export Files")
    print("=" * 60)

    # Load all datasets
    datasets = []
    total_records = 0

    for filepath in file_paths:
        try:
            data = dm.load_json(filepath)
            datasets.append(data)
            total_records += len(data)
            print(f"\n✓ Loaded {filepath}")
            print(f"  Records: {len(data)}")
        except Exception as e:
            print(f"\n✗ Failed to load {filepath}: {e}")
            return

    # Merge datasets
    print(f"\nMerging {len(datasets)} datasets...")
    merged = dm.merge_datasets(datasets, deduplicate_by=deduplicate_by)

    print(f"\nTotal records before merge: {total_records}")
    print(f"Total records after merge: {len(merged)}")

    if deduplicate_by:
        removed = total_records - len(merged)
        print(f"Duplicates removed: {removed} (by '{deduplicate_by}')")

    # Save merged data
    print(f"\nSaving merged data...")
    paths = dm.save_both_formats(merged, filename=output_name)

    print(f"\n✓ Merged data saved to:")
    print(f"  JSON: {paths['json']}")
    print(f"  CSV:  {paths['csv']}")

    # Show summary
    summary = dm.get_summary_stats(merged)
    print("\nMerged Data Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Merge multiple exported data files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge two files
  python scripts/merge_exports.py file1.json file2.json -o merged_leads

  # Merge with email deduplication
  python scripts/merge_exports.py file1.json file2.json -o merged_leads --dedupe email
        """
    )

    parser.add_argument(
        'files',
        nargs='+',
        help='JSON files to merge'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output filename (without extension)'
    )

    parser.add_argument(
        '--dedupe',
        help='Field to use for deduplication (e.g., email, phone)'
    )

    args = parser.parse_args()

    # Validate files exist
    for filepath in args.files:
        if not Path(filepath).exists():
            print(f"Error: File not found: {filepath}")
            sys.exit(1)

    # Merge files
    try:
        merge_files(args.files, args.output, args.dedupe)
        print("\n✓ Merge completed successfully!")
    except Exception as e:
        print(f"\n✗ Merge failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
