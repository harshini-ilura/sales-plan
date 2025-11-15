#!/usr/bin/env python3
"""
Utility script to view and manage exported data files
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_manager import DataManager


def list_exports():
    """List all exported files"""
    dm = DataManager()

    json_files = dm.list_exports("*.json")
    csv_files = dm.list_exports("*.csv")

    print("=" * 60)
    print("Exported Files")
    print("=" * 60)

    print("\nJSON Files:")
    if json_files:
        for i, file in enumerate(json_files, 1):
            stat = file.stat()
            size = stat.st_size / 1024  # KB
            mtime = datetime.fromtimestamp(stat.st_mtime)
            print(f"  {i}. {file.name}")
            print(f"     Size: {size:.2f} KB | Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("  No JSON files found")

    print("\nCSV Files:")
    if csv_files:
        for i, file in enumerate(csv_files, 1):
            stat = file.stat()
            size = stat.st_size / 1024  # KB
            mtime = datetime.fromtimestamp(stat.st_mtime)
            print(f"  {i}. {file.name}")
            print(f"     Size: {size:.2f} KB | Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("  No CSV files found")

    return json_files, csv_files


def view_file_summary(filepath):
    """View summary of a JSON export file"""
    dm = DataManager()

    try:
        data = dm.load_json(filepath)

        print("\n" + "=" * 60)
        print(f"File: {Path(filepath).name}")
        print("=" * 60)

        summary = dm.get_summary_stats(data)

        print("\nSummary Statistics:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

        if data:
            print("\nSample Record (first item):")
            print(json.dumps(data[0], indent=2))

    except Exception as e:
        print(f"Error reading file: {e}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='View and manage exported data files')
    parser.add_argument('--file', help='View summary of specific file')
    parser.add_argument('--latest', action='store_true', help='View summary of latest JSON export')

    args = parser.parse_args()

    dm = DataManager()

    if args.file:
        view_file_summary(args.file)
    elif args.latest:
        json_files = dm.list_exports("*.json")
        if json_files:
            view_file_summary(json_files[0])
        else:
            print("No JSON files found")
    else:
        list_exports()

        print("\n" + "=" * 60)
        print("Commands:")
        print("  --file <path>   View summary of specific file")
        print("  --latest        View summary of latest export")
        print("=" * 60)


if __name__ == '__main__':
    main()
