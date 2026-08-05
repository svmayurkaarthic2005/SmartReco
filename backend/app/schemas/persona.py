"""Persona and behavior analysis schemas"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class BehaviorSummaryResponse(BaseModel):
    """Response schema for behavior analysis"""
    user_id: str
    total_events: int
    unique_products_viewed: List[str]
    categories_explored: Dict[str, int]
    search_queries: List[str]
    avg_dwell_time: float
    cart_events: int
    wishlist_events: int
    enrollment_events: int
    repeat_visits: int
    category_switches: int
    session_durations: List[float]
    scroll_depth_avg: float
    exit_events: int
    recent_event_types: List[str]
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "total_events": 45,
                    "unique_products_viewed": ["prod-1", "prod-2", "prod-3"],
                    "categories_explored": {"python": 15, "machine-learning": 10, "data-science": 5},
                    "search_queries": ["Python for beginners", "machine learning basics"],
                    "avg_dwell_time": 135.5,
                    "cart_events": 3,
                    "wishlist_events": 2,
                    "enrollment_events": 1,
                    "repeat_visits": 4,
                    "category_switches": 6,
                    "session_durations": [300.0, 450.5, 200.0],
                    "scroll_depth_avg": 65.0,
                    "exit_events": 2,
                    "recent_event_types": ["view_product", "scroll", "time_on_page"]
                }
            ]
        }
    }


class PersonaResponse(BaseModel):
    """Response schema for persona classification"""
    persona: str  # Persona enum value
    confidence: float
    reasoning: str
    recommended_strategy: str
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "persona": "focused_builder",
                    "confidence": 0.75,
                    "reasoning": "User shows deep focus with 135s average dwell time in a dominant category, indicating commitment to mastering a specific domain.",
                    "recommended_strategy": "Recommend progressive content in their focused area. Suggest advanced courses and specializations in their dominant category."
                }
            ]
        }
    }


class UserAnalysisResponse(BaseModel):
    """Combined response with behavior and persona analysis"""
    behavior: BehaviorSummaryResponse
    persona: PersonaResponse
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "behavior": {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "total_events": 45,
                        "unique_products_viewed": ["prod-1", "prod-2"],
                        "categories_explored": {"python": 20, "ml": 15},
                        "search_queries": ["Python basics"],
                        "avg_dwell_time": 120.0,
                        "cart_events": 2,
                        "wishlist_events": 1,
                        "enrollment_events": 1,
                        "repeat_visits": 3,
                        "category_switches": 2,
                        "session_durations": [300.0, 450.0],
                        "scroll_depth_avg": 70.0,
                        "exit_events": 1,
                        "recent_event_types": ["view_product", "scroll"]
                    },
                    "persona": {
                        "persona": "focused_builder",
                        "confidence": 0.75,
                        "reasoning": "User shows deep focus in one category",
                        "recommended_strategy": "Recommend advanced content in focused area"
                    }
                }
            ]
        }
    }
