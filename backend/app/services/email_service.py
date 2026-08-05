"""
Email service for sending recovery and digest emails.

Uses aiosmtplib for async email sending with STARTTLS.
"""

import logging
from typing import List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from app.config import settings
from app.agents.recovery_agent import RecoveryResult
from app.langgraph.runner import RecommendationOutput


logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending personalized recommendation and recovery emails.
    
    Features:
    - Recovery emails for at-risk users
    - Weekly digest emails with recommendations
    - HTML email templates with inline CSS
    - Async SMTP with STARTTLS
    """
    
    def __init__(self):
        """Initialize email service with SMTP configuration from settings."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_user
        self.app_url = settings.app_url
    
    async def send_recovery_email(
        self,
        to_email: str,
        user_name: str,
        recovery: RecoveryResult
    ) -> bool:
        """
        Send re-engagement email to at-risk users.
        
        Email includes:
        - Warm, empathetic greeting
        - Recovery narrative (LLM-generated)
        - Top 3 recommended products (easiest first)
        - "Start Learning Again" CTA button
        
        Args:
            to_email: Recipient email address
            user_name: User's display name
            recovery: RecoveryResult with products and narrative
            
        Returns:
            True if email sent successfully, False otherwise
            
        Example:
            >>> service = EmailService()
            >>> success = await service.send_recovery_email(
            ...     "user@example.com",
            ...     "John",
            ...     recovery_result
            ... )
        """
        subject = f"We miss you, {user_name}! Your learning journey awaits 🎯"
        
        # Build email sections
        sections = []
        
        # Header
        sections.append(self._build_header())
        
        # Greeting
        sections.append(f"""
        <div style="padding: 30px; background: white; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: #2c3e50; margin-bottom: 16px;">Hi {user_name},</h2>
            <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                {recovery.recovery_narrative}
            </p>
        </div>
        """)
        
        # Product recommendations
        if recovery.recovery_products:
            products_html = '<div style="padding: 0 30px; margin-bottom: 30px;">'
            products_html += '<h3 style="color: #2c3e50; margin-bottom: 20px;">Start with these courses:</h3>'
            
            for i, product in enumerate(recovery.recovery_products[:3], 1):
                # Difficulty badge color
                difficulty_colors = {
                    "beginner": "#28a745",
                    "intermediate": "#ffc107",
                    "advanced": "#dc3545"
                }
                badge_color = difficulty_colors.get(product.difficulty.lower(), "#6c757d")
                
                products_html += f"""
                <div style="background: #f8f9fa; border-left: 4px solid {badge_color}; padding: 20px; margin-bottom: 16px; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <h4 style="color: #2c3e50; margin: 0 0 8px 0; font-size: 18px;">{i}. {product.title}</h4>
                            <p style="color: #6c757d; margin: 0 0 12px 0; font-size: 14px;">{product.description[:120]}...</p>
                            <div style="display: flex; gap: 12px; align-items: center;">
                                <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                                    {product.difficulty.upper()}
                                </span>
                                <span style="color: #6c757d; font-size: 14px;">
                                    {product.category.title()}
                                </span>
                            </div>
                        </div>
                        <div style="margin-left: 20px;">
                            <div style="background: #007bff; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold; font-size: 18px;">
                                ${product.price:.2f}
                            </div>
                        </div>
                    </div>
                </div>
                """
            
            products_html += '</div>'
            sections.append(products_html)
        
        # CTA button
        sections.append(f"""
        <div style="text-align: center; padding: 30px;">
            <a href="{self.app_url}/recommendations" 
               style="display: inline-block; background: #007bff; color: white; padding: 16px 48px; 
                      text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 18px;">
                Start Learning Again 🚀
            </a>
            <p style="color: #6c757d; font-size: 14px; margin-top: 16px;">
                Your personalized recommendations are waiting!
            </p>
        </div>
        """)
        
        # Footer
        sections.append(self._build_footer())
        
        # Assemble and send
        html_body = self._build_html(sections)
        return await self._send_email(to_email, subject, html_body)
    
    async def send_digest_email(
        self,
        to_email: str,
        user_name: str,
        output: RecommendationOutput
    ) -> bool:
        """
        Send weekly digest email with personalized recommendations.
        
        Email includes:
        - Personalized learning story
        - Ordered roadmap (numbered list)
        - Top 3 recommended products
        - Motivational CTA
        
        Args:
            to_email: Recipient email address
            user_name: User's display name
            output: RecommendationOutput with full narrative
            
        Returns:
            True if email sent successfully, False otherwise
            
        Example:
            >>> success = await service.send_digest_email(
            ...     "user@example.com",
            ...     "Sarah",
            ...     recommendation_output
            ... )
        """
        subject = f"Your Weekly Learning Recommendations, {user_name}! 📚"
        
        sections = []
        
        # Header
        sections.append(self._build_header())
        
        # Greeting and story
        sections.append(f"""
        <div style="padding: 30px; background: white; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: #2c3e50; margin-bottom: 16px;">Hi {user_name},</h2>
            <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                {output.narrative_result.personalized_story}
            </p>
        </div>
        """)
        
        # Learning roadmap
        if output.narrative_result.roadmap:
            roadmap_html = '<div style="padding: 0 30px; margin-bottom: 30px;">'
            roadmap_html += '<h3 style="color: #2c3e50; margin-bottom: 16px;">Your Learning Roadmap:</h3>'
            roadmap_html += '<ol style="color: #34495e; font-size: 16px; line-height: 2; padding-left: 24px;">'
            
            for course in output.narrative_result.roadmap[:5]:
                roadmap_html += f'<li style="margin-bottom: 8px;">{course}</li>'
            
            roadmap_html += '</ol></div>'
            sections.append(roadmap_html)
        
        # Top 3 products
        if output.ranked_products:
            products_html = '<div style="padding: 0 30px; margin-bottom: 30px;">'
            products_html += '<h3 style="color: #2c3e50; margin-bottom: 20px;">Start Here:</h3>'
            
            for i, product in enumerate(output.ranked_products[:3], 1):
                difficulty_colors = {
                    "beginner": "#28a745",
                    "intermediate": "#ffc107",
                    "advanced": "#dc3545"
                }
                badge_color = difficulty_colors.get(product.difficulty.lower(), "#6c757d")
                
                # Get product explanation
                explanation = output.narrative_result.product_explanations.get(
                    product.product_id,
                    "Highly recommended for your learning path."
                )
                
                products_html += f"""
                <div style="background: #f8f9fa; border-left: 4px solid {badge_color}; padding: 20px; margin-bottom: 16px; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <h4 style="color: #2c3e50; margin: 0 0 8px 0; font-size: 18px;">{i}. {product.title}</h4>
                            <p style="color: #6c757d; margin: 0 0 8px 0; font-size: 14px; font-style: italic;">
                                "{explanation}"
                            </p>
                            <p style="color: #6c757d; margin: 0 0 12px 0; font-size: 14px;">{product.description[:150]}...</p>
                            <div style="display: flex; gap: 12px; align-items: center;">
                                <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                                    {product.difficulty.upper()}
                                </span>
                                <span style="color: #6c757d; font-size: 14px;">
                                    {product.category.title()}
                                </span>
                                <span style="color: #6c757d; font-size: 14px;">
                                    ⭐ Score: {product.final_score:.2f}
                                </span>
                            </div>
                        </div>
                        <div style="margin-left: 20px;">
                            <div style="background: #007bff; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold; font-size: 18px;">
                                ${product.price:.2f}
                            </div>
                        </div>
                    </div>
                </div>
                """
            
            products_html += '</div>'
            sections.append(products_html)
        
        # CTA
        sections.append(f"""
        <div style="text-align: center; padding: 30px;">
            <a href="{self.app_url}/recommendations" 
               style="display: inline-block; background: #007bff; color: white; padding: 16px 48px; 
                      text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 18px;">
                {output.narrative_result.motivational_cta}
            </a>
            <p style="color: #6c757d; font-size: 14px; margin-top: 16px;">
                Personalized just for you based on your learning behavior
            </p>
        </div>
        """)
        
        # Footer
        sections.append(self._build_footer())
        
        html_body = self._build_html(sections)
        return await self._send_email(to_email, subject, html_body)
    
    def _build_header(self) -> str:
        """Build email header with logo."""
        return """
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <h1 style="color: white; margin: 0; font-size: 32px; font-weight: bold;">
                🎓 SmartReco
            </h1>
            <p style="color: rgba(255, 255, 255, 0.9); margin: 8px 0 0 0; font-size: 14px;">
                Your AI-Powered Learning Companion
            </p>
        </div>
        """
    
    def _build_footer(self) -> str:
        """Build email footer with unsubscribe link."""
        return """
        <div style="text-align: center; padding: 30px; background: #f8f9fa; border-top: 1px solid #dee2e6;">
            <p style="color: #6c757d; font-size: 14px; margin: 0 0 8px 0;">
                SmartReco - Behavioral AI Recommendation Platform
            </p>
            <p style="color: #6c757d; font-size: 12px; margin: 0;">
                <a href="#" style="color: #007bff; text-decoration: none;">Unsubscribe</a> | 
                <a href="#" style="color: #007bff; text-decoration: none;">Update Preferences</a> | 
                <a href="#" style="color: #007bff; text-decoration: none;">View in Browser</a>
            </p>
        </div>
        """
    
    def _build_html(self, sections: List[str]) -> str:
        """
        Assemble full HTML email with inline CSS.
        
        Args:
            sections: List of HTML section strings
            
        Returns:
            Complete HTML email string
        """
        sections_html = "\n".join(sections)
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartReco Recommendations</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f0f2f5;">
    <div style="max-width: 600px; margin: 0 auto; background: white;">
        {sections_html}
    </div>
</body>
</html>
        """
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str
    ) -> bool:
        """
        Send email via SMTP with STARTTLS.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject
            
            # Attach HTML
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Send via SMTP
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
