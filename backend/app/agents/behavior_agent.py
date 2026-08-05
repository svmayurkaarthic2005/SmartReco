"""Behavior Analysis Agent - Analyzes user interaction patterns"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventType
from app.models.product import Product
from app.observability.langsmith_client import trace_run


@dataclass
class BehaviorSummary:
    """Summary of user behavioral patterns"""
    user_id: str
    total_events: int
    unique_products_viewed: List[str] = field(default_factory=list)
    categories_explored: Dict[str, int] = field(default_factory=dict)  # category → count/weight
    search_queries: List[str] = field(default_factory=list)
    avg_dwell_time: float = 0.0
    cart_events: int = 0
    wishlist_events: int = 0
    enrollment_events: int = 0
    repeat_visits: int = 0
    category_switches: int = 0
    session_durations: List[float] = field(default_factory=list)
    scroll_depth_avg: float = 0.0
    exit_events: int = 0
    recent_product_titles: List[str] = field(default_factory=list)
    enrolled_product_titles: List[str] = field(default_factory=list)
    enrolled_product_ids: List[str] = field(default_factory=list)
    last_viewed_product_title: Optional[str] = None
    last_viewed_category: Optional[str] = None
    viewed_prices: List[float] = field(default_factory=list)
    avg_budget: float = 0.0
    min_budget: float = 0.0
    max_budget: float = 0.0
    viewed_difficulties: List[str] = field(default_factory=list)
    dominant_difficulty: str = 'intermediate'
    viewed_durations: List[float] = field(default_factory=list)
    avg_duration_preference: float = 0.0


class BehaviorAgent:
    """
    Analyzes user behavioral patterns from event data.
    
    Aggregates events to produce behavioral insights:
    - Content preferences (products, categories)
    - Engagement metrics (dwell time, scroll depth)
    - Purchase intent signals (cart, wishlist, enrollment)
    - Navigation patterns (category switches, repeat visits)
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize BehaviorAgent.
        
        Args:
            db: Database session for querying events
        """
        self.db = db
    
    async def analyze(
        self,
        user_id: uuid.UUID,
        lookback_hours: int = 72,
        parent_run_id: Optional[str] = None
    ) -> BehaviorSummary:
        """
        Analyze user behavior within lookback window.
        
        Args:
            user_id: User UUID to analyze
            lookback_hours: Hours of history to analyze (default: 72 = 3 days)
            parent_run_id: Optional parent trace ID for nesting
            
        Returns:
            BehaviorSummary with aggregated behavioral metrics
            
        Example:
            >>> agent = BehaviorAgent(db)
            >>> summary = await agent.analyze(user_id, lookback_hours=168)  # 1 week
            >>> print(f"User viewed {len(summary.unique_products_viewed)} unique products")
        """
        with trace_run(
            name="behavior_analysis",
            run_type="chain",
            inputs={
                "user_id": str(user_id),
                "lookback_hours": lookback_hours
            },
            parent_run_id=parent_run_id,
            tags=["agent", "behavior"]
        ) as run_id:
            # Calculate cutoff timestamp
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            
            # Query all events for user within lookback window
            stmt = (
                select(Event)
                .where(Event.user_id == user_id)
                .where(Event.timestamp >= cutoff_time)
                .order_by(Event.timestamp.asc())
            )
            
            result = await self.db.execute(stmt)
            events = result.scalars().all()
            
            # If no events, return empty summary
            if not events:
                return BehaviorSummary(
                    user_id=str(user_id),
                    total_events=0
                )
            
            # Aggregate data using Python (not SQL) for flexibility
            summary = await self._aggregate_events(str(user_id), events)
            return summary
    
    async def _aggregate_events(
        self,
        user_id: str,
        events: List[Event]
    ) -> BehaviorSummary:
        """
        Aggregate raw event rows into BehaviorSummary.
        
        Uses Python aggregation for maximum flexibility in computing
        complex behavioral metrics.
        """
        summary = BehaviorSummary(
            user_id=user_id,
            total_events=len(events)
        )
        
        # Fetch associated products to resolve categories and titles
        product_uuids = [e.product_id for e in events if e.product_id]
        product_map: Dict[str, Product] = {}
        if product_uuids:
            prod_stmt = select(Product).where(Product.id.in_(product_uuids))
            prod_res = await self.db.execute(prod_stmt)
            for p in prod_res.scalars().all():
                product_map[str(p.id)] = p

        # Temporary tracking variables
        product_ids_seen = set()
        dwell_times = []
        scroll_depths = []
        session_start_times: Dict[str, float] = {}  # session_id → start timestamp
        session_end_times: Dict[str, float] = {}    # session_id → end timestamp
        last_category: Optional[str] = None
        category_switch_count = 0
        
        # Iterate through events to aggregate with recency weighting
        num_events = len(events)
        for idx, event in enumerate(events):
            event_type = event.event_type
            product_obj = product_map.get(str(event.product_id)) if event.product_id else None
            meta = event.event_metadata or {}
            category = meta.get('category') or (product_obj.category if product_obj else None)
            is_enrollment = (event_type == EventType.ENROLL or str(event_type).lower() in ("enroll", "enrollment"))
            
            # Recency multiplier (recent events weighted up to 3x higher)
            recency_weight = 1.0 + ((idx + 1) / num_events) * 2.0

            # Track unique products viewed
            if event.product_id and (event_type == EventType.VIEW_PRODUCT or is_enrollment):
                product_ids_seen.add(str(event.product_id))

            # Record titles, prices, difficulties, and durations
            if product_obj:
                summary.last_viewed_product_title = product_obj.title
                if product_obj.price is not None:
                    summary.viewed_prices.append(float(product_obj.price))

                if getattr(product_obj, 'difficulty_level', None):
                    diff_val = product_obj.difficulty_level.value.lower() if hasattr(product_obj.difficulty_level, 'value') else str(product_obj.difficulty_level).lower()
                    summary.viewed_difficulties.append(diff_val)

                if getattr(product_obj, 'duration_hours', None) is not None:
                    summary.viewed_durations.append(float(product_obj.duration_hours))

                if product_obj.title in summary.recent_product_titles:
                    summary.recent_product_titles.remove(product_obj.title)
                summary.recent_product_titles.insert(0, product_obj.title)

                if is_enrollment:
                    if product_obj.title in summary.enrolled_product_titles:
                        summary.enrolled_product_titles.remove(product_obj.title)
                    summary.enrolled_product_titles.insert(0, product_obj.title)
                    
                    if str(event.product_id) not in summary.enrolled_product_ids:
                        summary.enrolled_product_ids.append(str(event.product_id))

            # Track categories explored with intent weights and recency
            if category:
                summary.last_viewed_category = category
                base_w = 1
                if is_enrollment:
                    base_w = 10
                elif event_type in (EventType.ADD_TO_CART, EventType.WISHLIST):
                    base_w = 5
                elif event_type == EventType.VIEW_PRODUCT:
                    base_w = 3
                
                weighted_val = round(base_w * recency_weight)
                summary.categories_explored[category] = summary.categories_explored.get(category, 0) + weighted_val
                
                if last_category and last_category != category:
                    category_switch_count += 1
                last_category = category
            
            # Track search queries
            if event_type == EventType.SEARCH and event.search_query:
                summary.search_queries.append(event.search_query)
            
            # Collect dwell times
            if event.dwell_time is not None and event.dwell_time > 0:
                dwell_times.append(event.dwell_time)
            
            # Count cart events
            if event_type == EventType.ADD_TO_CART:
                summary.cart_events += 1
            
            # Count wishlist events
            if event_type == EventType.WISHLIST:
                summary.wishlist_events += 1
            
            # Count enrollment events
            if is_enrollment:
                summary.enrollment_events += 1
            
            # Count repeat visits
            if event_type == EventType.REPEAT_VISIT:
                summary.repeat_visits += 1
            
            # Track scroll depths
            if event_type == EventType.SCROLL:
                if event.event_metadata and 'depth_percent' in event.event_metadata:
                    scroll_depths.append(event.event_metadata['depth_percent'])
            
            # Count exit events
            if event_type == EventType.EXIT:
                summary.exit_events += 1
            
            # Track session timestamps for duration calculation
            session_id = event.session_id
            event_timestamp = event.timestamp.timestamp()
            
            if session_id not in session_start_times:
                session_start_times[session_id] = event_timestamp
            session_end_times[session_id] = event_timestamp
        
        # Compute derived metrics
        summary.unique_products_viewed = list(product_ids_seen)
        summary.category_switches = category_switch_count
        
        # Budget derived metrics
        if summary.viewed_prices:
            summary.avg_budget = sum(summary.viewed_prices) / len(summary.viewed_prices)
            summary.min_budget = min(summary.viewed_prices)
            summary.max_budget = max(summary.viewed_prices)

        # Dominant difficulty level metric
        if summary.viewed_difficulties:
            from collections import Counter
            diff_counts = Counter(summary.viewed_difficulties)
            summary.dominant_difficulty = diff_counts.most_common(1)[0][0]

        # Average course duration preference
        if summary.viewed_durations:
            summary.avg_duration_preference = sum(summary.viewed_durations) / len(summary.viewed_durations)
        
        # Average dwell time
        if dwell_times:
            summary.avg_dwell_time = sum(dwell_times) / len(dwell_times)
        
        # Average scroll depth
        if scroll_depths:
            summary.scroll_depth_avg = sum(scroll_depths) / len(scroll_depths)
        
        # Session durations (end - start for each session)
        for session_id in session_start_times:
            duration = session_end_times[session_id] - session_start_times[session_id]
            if duration > 0:
                summary.session_durations.append(duration)
        
        # Recent event types (last 20)
        summary.recent_event_types = [
            event.event_type.value for event in events[-20:]
        ]
        
        return summary
