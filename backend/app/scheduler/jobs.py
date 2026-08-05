"""
APScheduler background jobs for SmartReco.

Jobs:
1. retry_embeddings_job - Retry failed product embeddings every 30 minutes
2. nightly_recommendation_job - Send digest/recovery emails at 7 PM daily
3. cache_cleanup_job - Clean expired cache entries every hour
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.database import AsyncSessionLocal
from app.models import User, Event
from app.models.recommendation_cache import RecommendationCache
from app.services.email_service import EmailService
from app.services.recommendation_service import RecommendationService
from app.services.product_service import ProductService
from app.vector.embedding_service import EmbeddingService
from app.vector.chroma_client import get_chroma_client
from app.config import settings


logger = logging.getLogger(__name__)


async def retry_embeddings_job():
    """
    Retry generating embeddings for products with FAILED status.
    
    Runs every 30 minutes via APScheduler.
    
    Process:
    1. Query products with EmbeddingStatus.FAILED
    2. Retry embedding generation
    3. Update to INDEXED or keep as FAILED
    4. Log success/failure counts
    """
    logger.info("Starting retry_embeddings_job")
    
    try:
        async with AsyncSessionLocal() as db:
            # Initialize services
            embedding_service = EmbeddingService()
            chroma_client = get_chroma_client()
            product_service = ProductService(db, embedding_service, chroma_client)
            
            # Retry failed embeddings
            count = await product_service.retry_failed_embeddings()
            
            logger.info(f"retry_embeddings_job completed: {count} products updated")
            
    except Exception as e:
        logger.error(f"retry_embeddings_job failed: {e}", exc_info=True)


async def nightly_recommendation_job():
    """
    Generate and send recommendation digest emails to active users.
    
    Runs daily at 7 PM via APScheduler.
    
    Process:
    1. Query users with events in last 7 days
    2. Process in batches of 10 concurrently (Semaphore)
    3. Generate recommendations for each user
    4. Send recovery email if at-risk, otherwise digest email
    5. Log success/failure counts
    
    Performance:
    - Concurrent limit: 10 (avoid overwhelming LLM API)
    - Expected time: ~3s per user (LLM-dominated)
    - 1000 users = ~5 minutes with concurrency
    """
    logger.info("Starting nightly_recommendation_job")
    
    try:
        async with AsyncSessionLocal() as db:
            # Get active users (events in last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            stmt = (
                select(User.id, User.email, User.name)
                .join(Event, Event.user_id == User.id)
                .where(Event.timestamp >= seven_days_ago)
                .group_by(User.id, User.email, User.name)
                .having(func.count(Event.id) >= 5)  # At least 5 events
            )
            
            result = await db.execute(stmt)
            active_users = result.all()
            
            if not active_users:
                logger.info("No active users found")
                return
            
            logger.info(f"Processing {len(active_users)} active users")
            
            # Initialize services
            redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            recommendation_service = RecommendationService(db, redis_client)
            email_service = EmailService()
            
            # Process users concurrently with semaphore
            semaphore = asyncio.Semaphore(10)  # Limit concurrent users
            
            success_count = 0
            failure_count = 0
            recovery_count = 0
            digest_count = 0
            
            async def process_user(user_id, email, name):
                """Process single user with semaphore."""
                nonlocal success_count, failure_count, recovery_count, digest_count
                
                async with semaphore:
                    try:
                        # Generate recommendation
                        output = await recommendation_service.get_or_generate(
                            user_id=user_id,
                            user_name=name or email.split("@")[0]
                        )
                        
                        # Send appropriate email
                        if output.is_recovery_mode and output.recovery_result:
                            # Send recovery email
                            sent = await email_service.send_recovery_email(
                                to_email=email,
                                user_name=name or email.split("@")[0],
                                recovery=output.recovery_result
                            )
                            if sent:
                                recovery_count += 1
                                success_count += 1
                            else:
                                failure_count += 1
                        else:
                            # Send digest email
                            sent = await email_service.send_digest_email(
                                to_email=email,
                                user_name=name or email.split("@")[0],
                                output=output
                            )
                            if sent:
                                digest_count += 1
                                success_count += 1
                            else:
                                failure_count += 1
                        
                        logger.info(f"Processed user {user_id}: {'recovery' if output.is_recovery_mode else 'digest'}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process user {user_id}: {e}")
                        failure_count += 1
            
            # Create tasks for all users
            tasks = [
                process_user(user_id, email, name)
                for user_id, email, name in active_users
            ]
            
            # Execute all tasks
            await asyncio.gather(*tasks)
            
            # Close Redis
            await redis_client.close()
            
            logger.info(
                f"nightly_recommendation_job completed: "
                f"{success_count} success, {failure_count} failed, "
                f"{recovery_count} recovery, {digest_count} digest"
            )
            
    except Exception as e:
        logger.error(f"nightly_recommendation_job failed: {e}", exc_info=True)


async def cache_cleanup_job():
    """
    Clean up expired cache entries from recommendation_cache table.
    
    Runs every hour via APScheduler.
    
    Process:
    1. DELETE FROM recommendation_cache WHERE expires_at < NOW()
    2. Log count of deleted rows
    
    Performance:
    - Fast query (expires_at is indexed)
    - Expected time: < 100ms
    """
    logger.info("Starting cache_cleanup_job")
    
    try:
        async with AsyncSessionLocal() as db:
            # Delete expired cache entries
            stmt = delete(RecommendationCache).where(
                RecommendationCache.expires_at < datetime.utcnow()
            )
            
            result = await db.execute(stmt)
            await db.commit()
            
            deleted_count = result.rowcount
            
            logger.info(f"cache_cleanup_job completed: {deleted_count} expired entries deleted")
            
    except Exception as e:
        logger.error(f"cache_cleanup_job failed: {e}", exc_info=True)


async def persona_refresh_job():
    """
    Refresh persona classifications for users with new behavior.
    
    Optional job - can be enabled based on needs.
    
    Process:
    1. Query users with events since last persona update
    2. Re-run persona classification
    3. Update Redis cache
    """
    logger.info("Starting persona_refresh_job")
    
    try:
        async with AsyncSessionLocal() as db:
            # Implementation: Query users with behavior changes
            # Re-classify personas
            # Update Redis cache
            
            logger.info("persona_refresh_job completed")
            
    except Exception as e:
        logger.error(f"persona_refresh_job failed: {e}", exc_info=True)


async def analytics_aggregation_job():
    """
    Aggregate analytics data for dashboard.
    
    Optional job for business intelligence.
    
    Process:
    1. Count events by type
    2. Aggregate persona distribution
    3. Calculate recommendation quality metrics
    4. Store in analytics tables
    """
    logger.info("Starting analytics_aggregation_job")
    
    try:
        async with AsyncSessionLocal() as db:
            # Implementation: Aggregate various metrics
            # Store in analytics tables
            
            logger.info("analytics_aggregation_job completed")
            
    except Exception as e:
        logger.error(f"analytics_aggregation_job failed: {e}", exc_info=True)
