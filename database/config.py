"""
Database configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f'sqlite:///{Path(__file__).parent.parent}/data/sales_leads.db'
)

# For PostgreSQL, use format: postgresql://user:password@localhost/dbname
# For MySQL, use format: mysql+pymysql://user:password@localhost/dbname

# Alembic configuration
ALEMBIC_CONFIG = {
    'script_location': str(Path(__file__).parent / 'migrations'),
    'sqlalchemy.url': DATABASE_URL
}
