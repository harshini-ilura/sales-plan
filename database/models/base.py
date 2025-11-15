"""
Base model with audit and soft-delete functionality
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

Base = declarative_base()


class AuditMixin:
    """Mixin for audit columns"""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)


class SoftDeleteMixin:
    """Mixin for soft-delete functionality"""

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(100), nullable=True)

    def soft_delete(self, deleted_by=None):
        """Mark record as deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by

    def restore(self):
        """Restore soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None


class BaseModel(Base, AuditMixin, SoftDeleteMixin):
    """Base model with ID, audit, and soft-delete columns"""

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name"""
        return cls.__name__.lower() + 's'

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
