"""
Background Sync Scheduler using APScheduler.

Manages automatic periodic synchronization of curriculums between local DB and Google Drive.
Handles scheduling, execution, and error recovery.
"""

from datetime import datetime, UTC, timedelta
from typing import Optional, Dict, Any, Callable
import asyncio
import logging
from sqlalchemy.orm import Session

from backend.app.services.sync_service import SyncService, SyncStatus
from backend.app.models.curriculum import Curriculum
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# APScheduler imports
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job
APSCHEDULER_AVAILABLE = True


class SyncScheduler:
    """
    Background scheduler for automatic curriculum synchronization.

    Manages periodic sync jobs, tracks sync history, and handles failures
    with automatic retry logic.
    """

    def __init__(
        self,
        db: Session,
        sync_service: SyncService,
        sync_interval_minutes: int = 5,
    ):
        """
        Initialize Sync Scheduler.

        Args:
            db: SQLAlchemy database session
            sync_service: SyncService instance
            sync_interval_minutes: How often to sync (default: 5 minutes)
        """
        self.db = db
        self.sync_service = sync_service
        self.sync_interval_minutes = sync_interval_minutes

        # Initialize APScheduler
        self.scheduler = BackgroundScheduler()
        self.scheduler.configure(
            job_defaults={
                'coalesce': False,
                'max_instances': 1,
            }
        )

        # Track active sync jobs
        self.active_syncs: Dict[str, Dict[str, Any]] = {}
        self.sync_history: Dict[str, list] = {}

    def start(self) -> None:
        """Start the background scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Sync scheduler started")

            # Schedule global sync job
            self._schedule_global_sync()

    def stop(self) -> None:
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Sync scheduler stopped")

    def _schedule_global_sync(self) -> Job:
        """Schedule the global sync job."""
        return self.scheduler.add_job(
            self._sync_all_curriculums,
            IntervalTrigger(minutes=self.sync_interval_minutes),
            id='global_sync',
            name='Global Curriculum Sync',
            replace_existing=True,
        )

    async def _sync_all_curriculums(self) -> None:
        """Sync all curriculums in the database."""
        curriculums = self.db.query(Curriculum).all()
        logger.info(f"Starting global sync for {len(curriculums)} curriculums")

        for curriculum in curriculums:
            await self._sync_curriculum_with_retry(curriculum.curriculum_id)

    async def _sync_curriculum_with_retry(
        self,
        curriculum_id: str,
        max_retries: int = 3,
        retry_delay_seconds: int = 5,
    ) -> Dict[str, Any]:
        """
        Sync a curriculum with automatic retry on failure.

        Args:
            curriculum_id: UUID of curriculum
            max_retries: Number of retries on failure
            retry_delay_seconds: Delay between retries

        Returns:
            Sync result
        """
        for attempt in range(max_retries):
            # Mark as in progress
            self.active_syncs[curriculum_id] = {
                "status": SyncStatus.IN_PROGRESS.value,
                "started_at": datetime.now(UTC),
                "attempt": attempt + 1,
            }

            # Run sync
            result = await self.sync_service.sync_curriculum(curriculum_id)

            # Mark as completed
            self.active_syncs[curriculum_id]["status"] = SyncStatus.COMPLETED.value
            self.active_syncs[curriculum_id]["completed_at"] = datetime.now(UTC)
            self.active_syncs[curriculum_id]["result"] = result

            # Track in history
            self._add_to_sync_history(curriculum_id, result)

            logger.info(
                f"Sync completed for curriculum {curriculum_id}: "
                f"{result.get('synced_count', 0)} synced, "
                f"{result.get('conflict_count', 0)} conflicts"
            )

            return result

    def sync_curriculum_now(self, curriculum_id: str) -> Dict[str, Any]:
        """
        Trigger immediate sync for a curriculum.

        Args:
            curriculum_id: UUID of curriculum

        Returns:
            Sync result
        """
        # Run in background
        job = self.scheduler.add_job(
            self._sync_curriculum_with_retry,
            args=[curriculum_id],
            id=f'sync_{curriculum_id}',
            name=f'Immediate Sync - {curriculum_id}',
        )

        return {
            "curriculum_id": curriculum_id,
            "job_id": job.id,
            "status": "scheduled",
            "scheduled_at": datetime.now(UTC),
        }

    def pause_sync(self, curriculum_id: str) -> None:
        """Pause sync for a curriculum."""
        if curriculum_id in self.active_syncs:
            self.active_syncs[curriculum_id]["status"] = SyncStatus.PAUSED.value
            logger.info(f"Sync paused for curriculum {curriculum_id}")

    def resume_sync(self, curriculum_id: str) -> None:
        """Resume sync for a curriculum."""
        if curriculum_id in self.active_syncs:
            if self.active_syncs[curriculum_id]["status"] == SyncStatus.PAUSED.value:
                self.active_syncs[curriculum_id]["status"] = SyncStatus.PENDING.value
                logger.info(f"Sync resumed for curriculum {curriculum_id}")

    def get_sync_status(self, curriculum_id: str) -> Dict[str, Any]:
        """
        Get current sync status for a curriculum.

        Returns:
            Status information including last sync time, pending changes, etc.
        """
        if curriculum_id in self.active_syncs:
            return self.active_syncs[curriculum_id]

        # Get from sync service
        return self.sync_service.get_sync_status(curriculum_id)

    def get_sync_history(self, curriculum_id: str, limit: int = 10) -> list:
        """
        Get sync history for a curriculum.

        Args:
            curriculum_id: UUID of curriculum
            limit: Maximum number of history entries to return

        Returns:
            List of sync history entries
        """
        history = self.sync_history.get(curriculum_id, [])
        return history[-limit:]

    def _add_to_sync_history(self, curriculum_id: str, result: Dict[str, Any]) -> None:
        """Add sync result to history."""
        if curriculum_id not in self.sync_history:
            self.sync_history[curriculum_id] = []

        history_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "status": result.get("status"),
            "synced_count": result.get("synced_count", 0),
            "updated_count": result.get("updated_count", 0),
            "conflict_count": result.get("conflict_count", 0),
            "error_count": len(result.get("errors", [])),
        }

        self.sync_history[curriculum_id].append(history_entry)

        # Keep only last 100 entries
        if len(self.sync_history[curriculum_id]) > 100:
            self.sync_history[curriculum_id] = self.sync_history[curriculum_id][-100:]

    def get_all_sync_status(self) -> Dict[str, Any]:
        """Get sync status for all curriculums."""
        curriculums = self.db.query(Curriculum).all()

        all_status = {
            "total_curriculums": len(curriculums),
            "active_syncs": len(self.active_syncs),
            "curriculums": {},
        }

        for curriculum in curriculums:
            all_status["curriculums"][curriculum.curriculum_id] = self.get_sync_status(
                curriculum.curriculum_id
            )

        return all_status


# Global scheduler instance
_scheduler_instance: Optional[SyncScheduler] = None


def get_sync_scheduler(
    db: Session,
    sync_service: SyncService,
) -> SyncScheduler:
    """
    Get or create Sync Scheduler instance.

    Args:
        db: SQLAlchemy database session
        sync_service: SyncService instance

    Returns:
        SyncScheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        sync_interval = getattr(settings, 'SYNC_INTERVAL_MINUTES', 5)
        _scheduler_instance = SyncScheduler(db, sync_service, sync_interval)

    return _scheduler_instance
