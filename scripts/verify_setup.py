#!/usr/bin/env python3
"""
Setup verification script
Checks if all dependencies and configuration are properly set up
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_python_version():
    """Check Python version"""
    print("Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro}")
        print("  Error: Python 3.7+ required")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")

    required = ['requests', 'yaml', 'dotenv']
    missing = []

    for package in required:
        try:
            if package == 'yaml':
                import yaml
            elif package == 'dotenv':
                import dotenv
            else:
                __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            missing.append(package)

    if missing:
        print(f"\nError: Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False

    return True


def check_directories():
    """Check if required directories exist"""
    print("\nChecking directories...")

    required_dirs = [
        'config',
        'src',
        'scripts',
        'data/exports'
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ {dir_path}/ - NOT FOUND")
            all_exist = False

    return all_exist


def check_config_files():
    """Check if configuration files exist"""
    print("\nChecking configuration files...")

    files = {
        'config/config.yaml': True,
        '.env': False,  # Optional
        '.env.example': True,
    }

    all_exist = True
    for filepath, required in files.items():
        path = Path(filepath)
        if path.exists():
            print(f"  ✓ {filepath}")
        else:
            if required:
                print(f"  ✗ {filepath} - NOT FOUND (required)")
                all_exist = False
            else:
                print(f"  ⚠ {filepath} - NOT FOUND (optional)")

    return all_exist


def check_api_token():
    """Check if API token is configured"""
    print("\nChecking API token...")

    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv('APIFY_API_TOKEN')

    if token:
        masked_token = token[:8] + "..." + token[-4:] if len(token) > 12 else "***"
        print(f"  ✓ APIFY_API_TOKEN found ({masked_token})")
        return True
    else:
        print("  ✗ APIFY_API_TOKEN not found")
        print("    Set it in .env file or environment variables")
        return False


def check_modules():
    """Check if custom modules can be imported"""
    print("\nChecking custom modules...")

    modules = [
        'src.apify_client',
        'src.email_scraper',
        'src.phone_scraper',
        'src.data_manager'
    ]

    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module} - {e}")
            all_ok = False

    return all_ok


def test_api_connection():
    """Test API connection (optional)"""
    print("\nTesting API connection...")

    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv('APIFY_API_TOKEN')

    if not token:
        print("  ⚠ Skipped (no API token)")
        return True

    try:
        from src.apify_client import ApifyClient

        client = ApifyClient(token)
        # Try to get actor info
        info = client.get_actor_info('T1XDXWc1L92AfIJtd')

        if info:
            print(f"  ✓ API connection successful")
            print(f"    Actor: {info.get('name', 'Unknown')}")
            return True
        else:
            print("  ✗ API connection failed")
            return False

    except Exception as e:
        print(f"  ✗ API connection failed: {e}")
        return False


def main():
    """Main verification function"""
    print("=" * 60)
    print("Apify Lead Scraper - Setup Verification")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Config Files", check_config_files),
        ("API Token", check_api_token),
        ("Custom Modules", check_modules),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} check failed with exception: {e}")
            results[name] = False

    # Optional API connection test
    print("\n" + "-" * 60)
    print("Optional Tests")
    print("-" * 60)
    try:
        api_ok = test_api_connection()
        results["API Connection"] = api_ok
    except Exception as e:
        print(f"  ⚠ API connection test failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n✓ Setup verification completed successfully!")
        print("  You're ready to start scraping.")
        print("\nNext steps:")
        print("  python scripts/scrape_leads_apify.py --help")
        return 0
    else:
        print("\n✗ Setup verification failed!")
        print("  Please fix the issues above and run this script again.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
