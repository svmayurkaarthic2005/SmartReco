"""Recommendation schemas"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class RankedProductResponse(BaseModel):
    """Response schema for ranked product"""
    product_id: str
    title: str
    description: str
    category: str
    difficulty: str
    price: float
    tags: List[str]
    final_score: float
    rank_position: int
    score_breakdown: Dict[str, float]
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_id": "prod-123",
                    "title": "Advanced Python Programming",
                    "description": "Master Python with advanced techniques",
                    "category": "python",
                    "difficulty": "advanced",
                    "price": 99.99,
                    "tags": ["python", "programming", "advanced"],
                    "final_score": 0.892,
                    "rank_position": 1,
                    "score_breakdown": {
                        "semantic": 0.95,
                        "difficulty_match": 1.0,
                        "learning_progression": 0.5,
                        "price_fit": 0.5,
                        "tag_overlap": 0.67,
                        "freshness": 0.91
                    }
                }
            ]
        }
    }


class RecoveryResultResponse(BaseModel):
    """Recovery recommendation details"""
    is_at_risk: bool
    recovery_narrative: str
    email_subject: str
    email_body: str


class RecommendationHistoryResponse(BaseModel):
    """Historical recommendation summary"""
    id: str
    persona: str
    confidence: float
    product_count: int
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    """Complete personalized recommendation response with narrative"""
    user_id: str
    persona: str
    confidence: float
    learning_goal: str
    personalized_story: str
    roadmap: List[str]
    product_explanations: Dict[str, str]  # product_id -> reason
    motivational_cta: str
    ranked_products: List[RankedProductResponse]
    recovery_result: Optional[RecoveryResultResponse] = None
    is_recovery_mode: bool
    generated_at: datetime
    trace_id: str
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "user-123",
                    "persona": "focused_builder",
                    "confidence": 0.85,
                    "learning_goal": "Master Python for backend development",
                    "personalized_story": "You're on a focused journey to master Python. Your consistent exploration of advanced topics shows you're ready to take the next step. Let's solidify your backend skills with these hand-picked courses.",
                    "roadmap": ["Advanced Python Programming", "FastAPI Mastery", "PostgreSQL Deep Dive"],
                    "product_explanations": {
                        "prod-1": "Builds on your Python foundation with advanced patterns",
                        "prod-2": "Perfect next step to apply your skills in modern APIs"
                    },
                    "motivational_cta": "Start your next course today and level up your backend expertise!",
                    "ranked_products": [
                        {
                            "product_id": "prod-1",
                            "title": "Advanced Python",
                            "description": "...",
                            "category": "python",
                            "difficulty": "advanced",
                            "price": 99.99,
                            "tags": ["python"],
                            "final_score": 0.89,
                            "rank_position": 1,
                            "score_breakdown": {
                                "semantic": 0.95,
                                "difficulty_match": 1.0,
                                "learning_progression": 0.5,
                                "price_fit": 0.5,
                                "tag_overlap": 0.67,
                                "freshness": 0.91
                            }
                        }
                    ],
                    "recovery_result": None,
                    "is_recovery_mode": False,
                    "generated_at": "2026-08-04T10:30:00",
                    "trace_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            ]
        }
    )

