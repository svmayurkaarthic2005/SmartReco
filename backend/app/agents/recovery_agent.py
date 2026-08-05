"""Recovery Agent - Detects at-risk users and generates re-engagement content"""

import uuid
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import openai

from app.config import settings
from app.agents.behavior_agent import BehaviorSummary
from app.agents.ranking_agent import RankedProduct
from app.models.event import Event, EventType
from app.observability.langsmith_client import trace_run


# Initialize Mesh API client
mesh_client = openai.AsyncOpenAI(
    api_key=settings.mesh_api_key,
    base_url=settings.mesh_api_base_url
)


@dataclass
class RecoveryResult:
    """Result of recovery recommendation generation"""
    is_at_risk: bool
    recovery_narrative: str
    recovery_products: List[RankedProduct]  # Top 3, easiest first
    email_subject: str
    email_body: str  # HTML


class RecoveryAgent:
    """
    Detects at-risk users and generates re-engagement content.
    
    Risk Detection:
    - High exit events (> 5)
    - Low recent activity (< 3 events in 24h)
    - No enrollment in 7+ days
    
    Recovery Strategy:
    - Warm, encouraging messaging
    - Start with easiest courses
    - Email with HTML product cards
    """
    
    RECOVERY_SYSTEM_PROMPT = """You are a compassionate learning coach helping someone return to their educational journey.

Your task: Write a warm, encouraging 2-sentence re-engagement message.

Guidelines:
- Be empathetic, not pushy
- Acknowledge their absence gently
- Focus on their learning area
- Suggest starting with an easy win
- Keep it short (2 sentences max)
- Be personal and motivating

Example tone: "We noticed you were exploring Python recently. Why not pick up where you left off with a quick refresher course?"
"""
    
    async def detect_risk(
        self,
        user_id: uuid.UUID,
        summary: BehaviorSummary,
        db: AsyncSession,
        parent_run_id: Optional[str] = None
    ) -> bool:
        """
        Detect if user is at risk of dropping off.
        
        Criteria (ALL must be true):
        1. exit_events > 5
        2. events in last 24h < 3
        3. no enrollment in last 7 days
        
        Args:
            user_id: User UUID
            summary: Behavioral summary (should be recent, e.g., 72h lookback)
            db: Database session
            parent_run_id: Optional parent trace ID for nesting
            
        Returns:
            True if user is at risk
        """
        with trace_run(
            name="recovery_detection",
            run_type="chain",
            inputs={
                "user_id": str(user_id),
                "exit_events": summary.exit_events,
                "total_events": summary.total_events,
                "enrollment_events": summary.enrollment_events
            },
            parent_run_id=parent_run_id,
            tags=["agent", "recovery", "detection"]
        ) as run_id:
            if summary.exit_events <= 5:
                return False
            
            # Check recent activity (last 24 hours)
            cutoff_24h = datetime.utcnow() - timedelta(hours=24)
            stmt_recent = (
                select(Event)
                .where(Event.user_id == user_id)
                .where(Event.timestamp >= cutoff_24h)
            )
            result = await db.execute(stmt_recent)
            recent_events = result.scalars().all()
            
            if len(recent_events) >= 3:
                return False
            
            # Check enrollment in last 7 days
            cutoff_7d = datetime.utcnow() - timedelta(days=7)
            stmt_enrollment = (
                select(Event)
                .where(Event.user_id == user_id)
                .where(Event.event_type == EventType.ENROLL)
                .where(Event.timestamp >= cutoff_7d)
            )
            result = await db.execute(stmt_enrollment)
            enrollment_events = result.scalars().all()
            
            is_at_risk = len(enrollment_events) == 0
            return is_at_risk
    
    async def generate_recovery_recommendation(
        self,
        user_id: uuid.UUID,
        summary: BehaviorSummary,
        top_products: List[RankedProduct],
        user_name: str = "there"
    ) -> RecoveryResult:
        """
        Generate recovery recommendation for at-risk user.
        
        Args:
            user_id: User UUID
            summary: Behavioral summary
            top_products: Top-ranked products
            user_name: User's name for personalization
            
        Returns:
            RecoveryResult with narrative and email content
        """
        # Sort products by difficulty (easiest first for re-engagement)
        difficulty_order = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
        sorted_products = sorted(
            top_products[:5],  # Consider top 5
            key=lambda p: difficulty_order.get(p.difficulty, 1)
        )
        recovery_products = sorted_products[:3]
        
        # Get top category from behavior
        top_category = "your interests"
        if summary.categories_explored:
            top_category = max(
                summary.categories_explored.items(),
                key=lambda x: x[1]
            )[0]
        
        # Generate recovery narrative using LLM
        recovery_narrative = await self._generate_recovery_narrative(
            top_category,
            user_name
        )
        
        # Build email
        email_subject = f"We miss you, {user_name}! Your learning journey awaits 🎯"
        email_body = self._build_recovery_email(
            user_name,
            recovery_narrative,
            recovery_products
        )
        
        return RecoveryResult(
            is_at_risk=True,
            recovery_narrative=recovery_narrative,
            recovery_products=recovery_products,
            email_subject=email_subject,
            email_body=email_body
        )
    
    async def _generate_recovery_narrative(
        self,
        top_category: str,
        user_name: str
    ) -> str:
        """
        Generate personalized recovery narrative using LLM.
        """
        user_prompt = f"""Generate a warm, encouraging 2-sentence re-engagement message for a learner who was exploring {top_category}.

Their name is {user_name}.

Guidelines:
- Be empathetic, not pushy
- Mention their learning area ({top_category})
- Suggest starting with an easy win
- Keep it to 2 sentences
- Be encouraging and motivating

Return ONLY the message text (no JSON, no formatting)."""
        
        try:
            response = await mesh_client.chat.completions.create(
                model=settings.mesh_model,
                messages=[
                    {"role": "system", "content": self.RECOVERY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,  # Slightly higher for warmth
                max_tokens=200
            )
            
            narrative = response.choices[0].message.content.strip()
            
            # Remove quotes if present
            narrative = narrative.strip('"\'')
            
            return narrative
        
        except Exception as e:
            print(f"Recovery narrative generation error: {e}")
            # Fallback message
            return f"We noticed you were exploring {top_category} recently. Why not pick up where you left off with a quick refresher course?"
    
    def _build_recovery_email(
        self,
        user_name: str,
        recovery_narrative: str,
        recovery_products: List[RankedProduct]
    ) -> str:
        """
        Build HTML email with product cards.
        """
        # Build product cards HTML
        product_cards_html = ""
        for product in recovery_products:
            # Difficulty badge color
            badge_color = {
                'beginner': '#10b981',     # Green
                'intermediate': '#3b82f6', # Blue
                'advanced': '#8b5cf6'      # Purple
            }.get(product.difficulty, '#6b7280')
            
            product_cards_html += f"""
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 15px 0;">
                <h3 style="margin: 0 0 10px 0; color: #111827; font-size: 18px;">{product.title}</h3>
                <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">{product.description[:120]}...</p>
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <span style="background: {badge_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                        {product.difficulty.upper()}
                    </span>
                    <span style="color: #6b7280; font-size: 14px;">
                        {product.category}
                    </span>
                </div>
                <p style="margin: 0; color: #111827; font-size: 16px; font-weight: 700;">${product.price:.2f}</p>
            </div>
            """
        
        # Complete email HTML
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Come Back to Learning</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">SmartReco</h1>
                    <p style="margin: 10px 0 0 0; color: #e0e7ff; font-size: 16px;">Your Learning Journey Awaits</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 20px;">
                    <!-- Greeting -->
                    <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 24px;">Hi {user_name},</h2>
                    
                    <!-- Recovery Narrative -->
                    <p style="margin: 0 0 30px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                        {recovery_narrative}
                    </p>
                    
                    <!-- Courses Section -->
                    <h3 style="margin: 0 0 20px 0; color: #111827; font-size: 20px;">Start with These Easy Wins</h3>
                    
                    {product_cards_html}
                    
                    <!-- CTA Button -->
                    <div style="text-align: center; margin: 40px 0 20px 0;">
                        <a href="https://smartreco.com/dashboard" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                            Resume Learning
                        </a>
                    </div>
                    
                    <!-- Footer Message -->
                    <p style="margin: 30px 0 0 0; color: #6b7280; font-size: 14px; text-align: center; line-height: 1.5;">
                        We're here to support your learning journey.<br>
                        Start small, stay consistent, achieve greatness.
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                        © 2026 SmartReco. All rights reserved.
                    </p>
                    <p style="margin: 10px 0 0 0; color: #9ca3af; font-size: 12px;">
                        <a href="https://smartreco.com/unsubscribe" style="color: #9ca3af; text-decoration: underline;">Unsubscribe</a> | 
                        <a href="https://smartreco.com/preferences" style="color: #9ca3af; text-decoration: underline;">Email Preferences</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return email_html.strip()
