"""
Creator Style Fingerprint Service

Calculates creator personality/style based on implicit signals:
- Behavior events (template views, clicks, watch time)
- Calibration pair selections
- Remix performance results

Based on PDR FR-010: 암묵 신호 기반 스타일 추정
"""
from collections import Counter
from datetime import datetime, timedelta

from app.utils.time import utcnow, days_ago
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Import event store from events router (MVP: in-memory)
from app.routers.events import _event_store


@dataclass
class StyleFingerprint:
    """Creator style fingerprint output."""
    user_id: str
    tone: str  # humorous, informative, dramatic, neutral
    pacing: str  # fast, medium, slow
    hook_preferences: List[str]  # visual_shock, curiosity, problem
    visual_style: str  # polished, raw, minimalist
    confidence: float  # 0.0 - 1.0
    sample_count: int
    last_updated: datetime
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "tone": self.tone,
            "pacing": self.pacing,
            "hook_preferences": self.hook_preferences,
            "visual_style": self.visual_style,
            "confidence": self.confidence,
            "sample_count": self.sample_count,
            "last_updated": self.last_updated.isoformat(),
        }


class CreatorFingerprintService:
    """
    Calculates creator style fingerprint from implicit behavioral signals.
    
    No explicit questions asked - style is inferred from:
    1. Which templates they linger on (watch time)
    2. Which pairs they select in calibration
    3. Which patterns they successfully execute
    """
    
    # Tone mapping from template categories
    TONE_SIGNALS = {
        "meme": "humorous",
        "comedy": "humorous",
        "tutorial": "informative",
        "beauty": "polished",
        "lifestyle": "casual",
        "drama": "dramatic",
        "news": "informative",
    }
    
    # Hook pattern preferences
    HOOK_CATEGORIES = {
        "curiosity": ["curiosity_hook", "question", "mystery"],
        "visual_shock": ["visual_shock", "surprise", "reaction"],
        "problem": ["problem_solution", "how_to", "tutorial"],
        "emotional": ["emotional", "story", "dramatic"],
    }
    
    async def calculate_fingerprint(
        self,
        user_id: str,
        db: Optional[AsyncSession] = None,
    ) -> StyleFingerprint:
        """
        Calculate style fingerprint for a user.
        """
        # Get user's events
        user_events = self._get_user_events(user_id)
        
        if len(user_events) < 3:
            # Not enough data - return neutral fingerprint
            return StyleFingerprint(
                user_id=user_id,
                tone="neutral",
                pacing="medium",
                hook_preferences=["curiosity"],
                visual_style="neutral",
                confidence=0.1,
                sample_count=len(user_events),
                last_updated=utcnow(),
            )
        
        # Analyze events
        tone = self._infer_tone(user_events)
        pacing = self._infer_pacing(user_events)
        hook_prefs = self._infer_hook_preferences(user_events)
        visual_style = self._infer_visual_style(user_events)
        confidence = self._calculate_confidence(user_events)
        
        return StyleFingerprint(
            user_id=user_id,
            tone=tone,
            pacing=pacing,
            hook_preferences=hook_prefs,
            visual_style=visual_style,
            confidence=confidence,
            sample_count=len(user_events),
            last_updated=utcnow(),
        )
    
    def _get_user_events(self, user_id: str) -> List[dict]:
        """Get events for a specific user from in-memory store."""
        return [
            e for e in _event_store 
            if e.get("user_id") == user_id
        ]
    
    def _infer_tone(self, events: List[dict]) -> str:
        """Infer preferred tone from viewed content categories."""
        categories = []
        for event in events:
            if event.get("event_type") in ["page_view", "template_click", "video_watch"]:
                metadata = event.get("metadata", {})
                category = metadata.get("category")
                if category:
                    categories.append(category)
        
        if not categories:
            return "neutral"
        
        # Count and map to tones
        tone_counts = Counter()
        for cat in categories:
            tone = self.TONE_SIGNALS.get(cat.lower(), "neutral")
            tone_counts[tone] += 1
        
        return tone_counts.most_common(1)[0][0] if tone_counts else "neutral"
    
    def _infer_pacing(self, events: List[dict]) -> str:
        """Infer preferred pacing from watch behavior."""
        watch_times = []
        for event in events:
            if event.get("event_type") == "video_watch":
                metadata = event.get("metadata", {})
                watch_seconds = metadata.get("watch_seconds", 0)
                video_duration = metadata.get("video_duration", 60)
                if video_duration > 0:
                    completion_rate = watch_seconds / video_duration
                    watch_times.append(completion_rate)
        
        if not watch_times:
            return "medium"
        
        avg_completion = sum(watch_times) / len(watch_times)
        
        # Fast pacing preference = lower completion (short attention)
        if avg_completion < 0.5:
            return "fast"
        elif avg_completion > 0.8:
            return "slow"
        return "medium"
    
    def _infer_hook_preferences(self, events: List[dict]) -> List[str]:
        """Infer preferred hook patterns from interactions."""
        hook_counts = Counter()
        
        for event in events:
            metadata = event.get("metadata", {})
            hook_pattern = metadata.get("hook_pattern")
            
            if hook_pattern:
                # Map to category
                for category, patterns in self.HOOK_CATEGORIES.items():
                    if any(p in hook_pattern.lower() for p in patterns):
                        hook_counts[category] += 1
                        break
        
        if not hook_counts:
            return ["curiosity"]  # default
        
        # Return top 2 preferences
        return [h[0] for h in hook_counts.most_common(2)]
    
    def _infer_visual_style(self, events: List[dict]) -> str:
        """Infer preferred visual style."""
        styles = []
        for event in events:
            metadata = event.get("metadata", {})
            visual = metadata.get("visual_style") or metadata.get("visual_patterns")
            if visual:
                if isinstance(visual, list):
                    styles.extend(visual)
                else:
                    styles.append(visual)
        
        if not styles:
            return "neutral"
        
        style_counts = Counter(styles)
        top_style = style_counts.most_common(1)[0][0]
        
        # Normalize
        if any(s in top_style.lower() for s in ["polished", "aesthetic", "clean"]):
            return "polished"
        elif any(s in top_style.lower() for s in ["raw", "authentic", "casual"]):
            return "raw"
        elif any(s in top_style.lower() for s in ["minimal", "simple"]):
            return "minimalist"
        
        return "neutral"
    
    def _calculate_confidence(self, events: List[dict]) -> float:
        """Calculate confidence score based on signal quantity and quality."""
        base_confidence = min(1.0, len(events) / 20)  # Max at 20 events
        
        # Boost for diverse event types
        event_types = set(e.get("event_type") for e in events)
        diversity_boost = min(0.2, len(event_types) * 0.05)
        
        # Boost for recent activity
        recent_events = [
            e for e in events 
            if datetime.fromisoformat(e.get("timestamp", "2020-01-01")) 
               > days_ago(7)
        ]
        recency_boost = 0.1 if len(recent_events) > 3 else 0
        
        return round(min(1.0, base_confidence + diversity_boost + recency_boost), 2)


# Singleton instance
fingerprint_service = CreatorFingerprintService()
