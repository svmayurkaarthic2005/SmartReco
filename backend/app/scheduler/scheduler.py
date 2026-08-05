"""
APScheduler configuration and job registration.

Scheduler runs background jobs for:
- Embedding retries (every 30 minutes)
- Nightly recommendation emails (daily at 7 PM)
- Cache cleanup (every hour)
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from app.scheduler.jobs import (
    retry_embeddings_job,
    nightly_recommendation_job,
    cache_cleanup_job,
)
from app.config import settings


logger = logging.getLogger(__name__)


# Initialize scheduler
scheduler = AsyncIOScheduler(
    jobstores={"default": MemoryJobStore()},
    timezone=settings.scheduler_timezone,
)


def register_jobs():
    """
    Register all background jobs with APScheduler.
    
    Jobs:
    1. retry_embeddings_job - Every 30 minutes
    2. nightly_recommendation_job - Daily at 7 PM (19:00)
    3. cache_cleanup_job - Every hour
    
    Job IDs allow for job management (pause, resume, remove).
    """
    
    # Job 1: Retry failed embeddings every 30 minutes
    scheduler.add_job(
        retry_embeddings_job,
        trigger=IntervalTrigger(minutes=30),
        id="retry_embeddings_job",
        name="Retry Failed Embeddings",
        replace_existing=True,
        max_instances=1,  # Only one instance at a time
        coalesce=True,  # Combine missed runs
        misfire_grace_time=300,  # 5 minutes grace period
    )
    logger.info("Registered job: retry_embeddings_job (every 30 minutes)")
    
    # Job 2: Nightly recommendation emails at 7 PM
    scheduler.add_job(
        nightly_recommendation_job,
        trigger=CronTrigger(hour=19, minute=0),  # 7:00 PM daily
        id="nightly_recommendation_job",
        name="Nightly Recommendation Emails",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=900,  # 15 minutes grace period
    )
    logger.info("Registered job: nightly_recommendation_job (daily at 7 PM)")
    
    # Job 3: Cache cleanup every hour
    scheduler.add_job(
        cache_cleanup_job,
        trigger=IntervalTrigger(hours=1),
        id="cache_cleanup_job",
        name="Cache Cleanup",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=600,  # 10 minutes grace period
    )
    logger.info("Registered job: cache_cleanup_job (every hour)")


def start_scheduler():
    """
    Start the APScheduler.
    
    Called from FastAPI lifespan/startup event.
    
    Example:
        @app.on_event("startup")
        async def startup():
            start_scheduler()
    """
    if not settings.scheduler_enabled:
        logger.info("Scheduler is disabled by configuration")
        return
    
    try:
        # Register all jobs
        register_jobs()
        
        # Start scheduler
        scheduler.start()
        
        logger.info(
            f"APScheduler started successfully. "
            f"Timezone: {settings.scheduler_timezone}"
        )
        
        # Log scheduled jobs
        jobs = scheduler.get_jobs()
        logger.info(f"Active jobs: {len(jobs)}")
        for job in jobs:
            logger.info(
                f"  - {job.name} (ID: {job.id}): "
                f"Next run: {job.next_run_time}"
            )
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)


def shutdown_scheduler():
    """
    Shutdown the APScheduler gracefully.
    
    Called from FastAPI lifespan/shutdown event.
    
    Example:
        @app.on_event("shutdown")
        async def shutdown():
            shutdown_scheduler()
    """
    if not settings.scheduler_enabled:
        return
    
    try:
        if scheduler.running:
            scheduler.shutdown(wait=True)
            logger.info("APScheduler shutdown successfully")
    except Exception as e:
        logger.error(f"Error during scheduler shutdown: {e}", exc_info=True)


def pause_job(job_id: str):
    """
    Pause a specific job.
    
    Args:
        job_id: Job identifier (e.g., "retry_embeddings_job")
        
    Example:
        pause_job("nightly_recommendation_job")
    """
    try:
        scheduler.pause_job(job_id)
        logger.info(f"Job paused: {job_id}")
    except Exception as e:
        logger.error(f"Failed to pause job {job_id}: {e}")


def resume_job(job_id: str):
    """
    Resume a paused job.
    
    Args:
        job_id: Job identifier
        
    Example:
        resume_job("nightly_recommendation_job")
    """
    try:
        scheduler.resume_job(job_id)
        logger.info(f"Job resumed: {job_id}")
    except Exception as e:
        logger.error(f"Failed to resume job {job_id}: {e}")


def trigger_job_now(job_id: str):
    """
    Manually trigger a job immediately.
    
    Args:
        job_id: Job identifier
        
    Example:
        trigger_job_now("retry_embeddings_job")
    """
    try:
        job = scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now())
            logger.info(f"Job triggered: {job_id}")
        else:
            logger.error(f"Job not found: {job_id}")
    except Exception as e:
        logger.error(f"Failed to trigger job {job_id}: {e}")


def get_job_status(job_id: str) -> dict:
    """
    Get status information for a specific job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Dictionary with job status details
        
    Example:
        >>> status = get_job_status("nightly_recommendation_job")
        >>> print(status["next_run_time"])
    """
    try:
        job = scheduler.get_job(job_id)
        if job:
            return {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
                "pending": job.pending,
            }
        else:
            return {"error": f"Job not found: {job_id}"}
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        return {"error": str(e)}


# Export for easy import
__all__ = [
    "scheduler",
    "start_scheduler",
    "shutdown_scheduler",
    "pause_job",
    "resume_job",
    "trigger_job_now",
    "get_job_status",
]
