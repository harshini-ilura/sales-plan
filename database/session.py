"""
Database session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from .config import DATABASE_URL

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create thread-safe session
ScopedSession = scoped_session(SessionLocal)


def get_session():
    """
    Get a new database session

    Returns:
        Session instance
    """
    return SessionLocal()


@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations

    Usage:
        with session_scope() as session:
            session.add(obj)
            # Changes are automatically committed
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """
    Initialize database - create all tables
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Drop all tables (use with caution!)
    """
    from .models import Base
    Base.metadata.drop_all(bind=engine)
