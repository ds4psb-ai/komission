"""
Notification Service - S-tier Outlier Alerts
Based on 14_OUTLIER_CRAWLER_INTEGRATION_DESIGN.md L271

Sends Slack/Email notifications when S-tier outliers are discovered.
"""
import os
import logging
from typing import Optional, List
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class NotificationService:
    """
    알림 서비스
    S-tier 아웃라이어 발견 시 Slack/Email 알림 전송
    """
    
    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.alert_email = os.getenv("ALERT_EMAIL")
        self.enabled = bool(self.slack_webhook or self.alert_email)
    
    async def notify_s_tier_outlier(
        self,
        outlier_id: str,
        title: str,
        platform: str,
        video_url: str,
        outlier_score: float,
        view_count: int,
    ) -> bool:
        """
        S-tier 아웃라이어 알림 전송
        
        Args:
            outlier_id: 아웃라이어 ID
            title: 콘텐츠 제목
            platform: 플랫폼 (youtube/tiktok/instagram)
            video_url: 원본 URL
            outlier_score: 아웃라이어 점수 (≥500 for S-tier)
            view_count: 조회수
        
        Returns:
            성공 여부
        """
        if not self.enabled:
            logger.warning("Notifications disabled: No SLACK_WEBHOOK_URL or ALERT_EMAIL configured")
            return False
        
        # Format message
        message = self._format_s_tier_message(
            outlier_id=outlier_id,
            title=title,
            platform=platform,
            video_url=video_url,
            outlier_score=outlier_score,
            view_count=view_count,
        )
        
        success = True
        
        # Send Slack notification
        if self.slack_webhook:
            slack_success = await self._send_slack(message)
            success = success and slack_success
        
        # TODO: Email notification (if needed)
        # if self.alert_email:
        #     email_success = await self._send_email(message)
        #     success = success and email_success
        
        return success
    
    async def notify_batch_complete(
        self,
        job_id: str,
        platforms: List[str],
        total_collected: int,
        total_inserted: int,
        s_tier_count: int,
    ) -> bool:
        """
        크롤링 배치 완료 알림
        """
        if not self.enabled:
            return False
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🤖 Crawler Batch Complete",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Job ID:*\n`{job_id}`"},
                        {"type": "mrkdwn", "text": f"*Platforms:*\n{', '.join(platforms)}"},
                        {"type": "mrkdwn", "text": f"*Collected:*\n{total_collected}"},
                        {"type": "mrkdwn", "text": f"*Inserted:*\n{total_inserted}"},
                    ]
                },
            ]
        }
        
        if s_tier_count > 0:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🏆 *{s_tier_count} S-Tier outliers found!*"
                }
            })
        
        if self.slack_webhook:
            return await self._send_slack(message)
        
        return True
    
    def _format_s_tier_message(
        self,
        outlier_id: str,
        title: str,
        platform: str,
        video_url: str,
        outlier_score: float,
        view_count: int,
    ) -> dict:
        """Slack Block Kit 메시지 포맷"""
        platform_emoji = {
            "youtube": "📺",
            "tiktok": "🎵",
            "instagram": "📸",
        }.get(platform.lower(), "🎬")
        
        # Format view count
        if view_count >= 1_000_000:
            views_str = f"{view_count / 1_000_000:.1f}M"
        elif view_count >= 1_000:
            views_str = f"{view_count / 1_000:.0f}K"
        else:
            views_str = str(view_count)
        
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🏆 S-Tier Outlier Detected!",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{platform_emoji} *{platform.upper()}*\n{title[:100]}..."
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Original",
                            "emoji": True
                        },
                        "url": video_url,
                        "action_id": "view_original"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Score:*\n🔥 {outlier_score:.0f}x"},
                        {"type": "mrkdwn", "text": f"*Views:*\n👁️ {views_str}"},
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Outlier ID: `{outlier_id}` | Detected: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ]
        }
    
    async def _send_slack(self, message: dict) -> bool:
        """Slack Webhook으로 메시지 전송"""
        if not self.slack_webhook:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook,
                    json=message,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info("Slack notification sent successfully")
                    return True
                else:
                    logger.error(f"Slack notification failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return False


# Singleton instance
notification_service = NotificationService()


# Helper function for easy import
async def notify_s_tier(
    outlier_id: str,
    title: str,
    platform: str,
    video_url: str,
    outlier_score: float,
    view_count: int,
) -> bool:
    """S-tier 알림 전송 헬퍼"""
    return await notification_service.notify_s_tier_outlier(
        outlier_id=outlier_id,
        title=title,
        platform=platform,
        video_url=video_url,
        outlier_score=outlier_score,
        view_count=view_count,
    )
