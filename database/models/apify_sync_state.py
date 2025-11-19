"""
Apify Sync State model - tracks synchronization status
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Index
from datetime import datetime
from .base import BaseModel


class ApifySyncState(BaseModel):
    """
    Tracks synchronization state for Apify actors and runs
    """
    __tablename__ = 'apify_sync_states'

    # Actor information
    actor_id = Column(String(100), nullable=False, index=True)
    actor_name = Column(String(255), nullable=True)

    # Run information
    run_id = Column(String(100), nullable=False, unique=True)
    dataset_id = Column(String(100), nullable=True)

    # Sync status
    sync_status = Column(String(50), nullable=False, default='pending')  # pending, syncing, completed, failed
    last_sync_at = Column(DateTime, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)

    # Run details
    run_status = Column(String(50), nullable=True)  # READY, RUNNING, SUCCEEDED, FAILED, etc.
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Results tracking
    total_records = Column(Integer, default=0)
    synced_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    duplicate_records = Column(Integer, default=0)

    # Input parameters
    input_params = Column(JSON, nullable=True)

    # Error tracking
    error_message = Column(String(500), nullable=True)
    error_details = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0)

    # Cost tracking
    compute_units = Column(Integer, nullable=True)
    cost_usd = Column(String(20), nullable=True)

    # Additional metadata
    meta_data = Column('metadata', JSON, nullable=True)  # Using 'metadata' as DB column name, 'meta_data' as Python attr

    def __repr__(self):
        return f"<ApifySyncState(id={self.id}, run_id='{self.run_id}', status='{self.sync_status}')>"

    def mark_completed(self, synced_count, failed_count=0, duplicate_count=0):
        """Mark sync as completed"""
        self.sync_status = 'completed'
        self.last_sync_at = datetime.utcnow()
        self.synced_records = synced_count
        self.failed_records = failed_count
        self.duplicate_records = duplicate_count

    def mark_failed(self, error_message):
        """Mark sync as failed"""
        self.sync_status = 'failed'
        self.last_sync_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1


# Indexes
Index('idx_sync_actor_status', ApifySyncState.actor_id, ApifySyncState.sync_status)
Index('idx_sync_run', ApifySyncState.run_id)
Index('idx_sync_status_time', ApifySyncState.sync_status, ApifySyncState.last_sync_at)
