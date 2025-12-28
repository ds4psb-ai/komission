"""
Gamification Router - Badges, Streaks, Leaderboard, Daily Missions
Expert Recommendation Implementation
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.utils.time import utcnow, utc_date_today
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models import (
    User, RemixNode, UserBadge, BadgeType, 
    UserStreak, DailyMission, MissionType
)
from app.routers.auth import get_current_user

router = APIRouter()


# --- Schemas ---

class BadgeResponse(BaseModel):
    badge_type: str
    emoji: str
    name: str
    description: str
    earned_at: datetime

    class Config:
        from_attributes = True


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[datetime]
    streak_points_earned: int
    next_milestone: int  # Days until next streak reward


class MissionResponse(BaseModel):
    mission_type: str
    name: str
    description: str
    points: int
    completed: bool
    completed_at: Optional[datetime]


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    user_name: Optional[str]
    profile_image: Optional[str]
    total_royalty: int
    streak_days: int
    badge_count: int


# Badge metadata
BADGE_METADATA = {
    BadgeType.FIRST_FORK: {"emoji": "🍽️", "name": "첫 포크", "description": "첫 번째 리믹스 완료"},
    BadgeType.VIRAL_MAKER: {"emoji": "🚀", "name": "바이럴 메이커", "description": "성장률 +50% 이상 달성"},
    BadgeType.SPEED_RUNNER: {"emoji": "⚡", "name": "스피드러너", "description": "24시간 내 3개 리믹스"},
    BadgeType.ORIGINAL_CREATOR: {"emoji": "👨‍👧‍👦", "name": "오리지널 크리에이터", "description": "내 포크가 또 Fork됨"},
    BadgeType.COLLABORATOR: {"emoji": "🤝", "name": "협력자", "description": "퀘스트에서 수익 얻기"},
    BadgeType.STREAK_3: {"emoji": "🔥", "name": "3일 연속", "description": "3일 연속 업로드"},
    BadgeType.STREAK_7: {"emoji": "🔥🔥", "name": "7일 연속", "description": "7일 연속 업로드"},
    BadgeType.STREAK_30: {"emoji": "🔥🔥🔥", "name": "30일 연속", "description": "30일 연속 업로드"},
}

MISSION_METADATA = {
    MissionType.APP_OPEN: {"name": "앱 접속", "description": "오늘 앱에 접속했어요", "points": 50},
    MissionType.FIRST_FILMING: {"name": "첫 촬영", "description": "오늘 첫 리믹스 완료", "points": 100},
    MissionType.QUEST_ACCEPT: {"name": "퀘스트 수락", "description": "O2O 퀘스트 수락", "points": 150},
    MissionType.FORK_CREATE: {"name": "포크 생성", "description": "새로운 리믹스 생성", "points": 100},
}


# --- Endpoints ---

@router.get("/badges", response_model=List[BadgeResponse])
async def get_my_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all badges earned by current user"""
    result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == current_user.id)
        .order_by(UserBadge.earned_at.desc())
    )
    badges = result.scalars().all()
    
    return [
        BadgeResponse(
            badge_type=b.badge_type.value if hasattr(b.badge_type, 'value') else b.badge_type,
            emoji=BADGE_METADATA.get(b.badge_type, {}).get("emoji", "🏅"),
            name=BADGE_METADATA.get(b.badge_type, {}).get("name", "Unknown"),
            description=BADGE_METADATA.get(b.badge_type, {}).get("description", ""),
            earned_at=b.earned_at
        )
        for b in badges
    ]


@router.get("/streak", response_model=StreakResponse)
async def get_my_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's streak information"""
    result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == current_user.id)
    )
    streak = result.scalar_one_or_none()
    
    if not streak:
        # Create new streak record
        streak = UserStreak(user_id=current_user.id)
        db.add(streak)
        await db.commit()
        await db.refresh(streak)
    
    # Calculate next milestone
    current = streak.current_streak
    if current < 3:
        next_milestone = 3 - current
    elif current < 7:
        next_milestone = 7 - current
    elif current < 30:
        next_milestone = 30 - current
    else:
        next_milestone = 0  # Already at max
    
    return StreakResponse(
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        last_activity_date=streak.last_activity_date,
        streak_points_earned=streak.streak_points_earned,
        next_milestone=next_milestone
    )


@router.post("/streak/check-in")
async def check_in_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check in for daily streak.
    Called when user performs any qualifying action (filming, fork, etc.)
    """
    result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == current_user.id)
    )
    streak = result.scalar_one_or_none()
    
    if not streak:
        streak = UserStreak(user_id=current_user.id)
        db.add(streak)
    
    today = utcnow().date()
    last_activity = streak.last_activity_date.date() if streak.last_activity_date else None
    
    points_earned = 0
    new_badges = []
    
    if last_activity == today:
        # Already checked in today
        return {
            "status": "already_checked_in",
            "current_streak": streak.current_streak,
            "points_earned": 0,
            "new_badges": []
        }
    elif last_activity == today - timedelta(days=1):
        # Consecutive day - increase streak
        streak.current_streak += 1
    else:
        # Streak broken - reset
        streak.current_streak = 1
    
    streak.last_activity_date = utcnow()
    
    # Update longest streak
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak
    
    # Check streak milestones
    if streak.current_streak == 3:
        points_earned = 500
        new_badges.append(BadgeType.STREAK_3)
    elif streak.current_streak == 7:
        points_earned = 2000
        new_badges.append(BadgeType.STREAK_7)
    elif streak.current_streak == 30:
        points_earned = 30000
        new_badges.append(BadgeType.STREAK_30)
    
    # Award points
    if points_earned > 0:
        current_user.k_points += points_earned
        streak.streak_points_earned += points_earned
    
    # Award badges
    for badge_type in new_badges:
        badge = UserBadge(
            user_id=current_user.id,
            badge_type=badge_type
        )
        db.add(badge)
    
    await db.commit()
    
    return {
        "status": "checked_in",
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "points_earned": points_earned,
        "new_badges": [b.value for b in new_badges]
    }


@router.get("/missions/daily", response_model=List[MissionResponse])
async def get_daily_missions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get today's daily missions and their completion status"""
    today = utc_date_today()
    
    # Get existing missions for today
    result = await db.execute(
        select(DailyMission)
        .where(
            and_(
                DailyMission.user_id == current_user.id,
                DailyMission.mission_date >= today
            )
        )
    )
    existing_missions = {m.mission_type: m for m in result.scalars().all()}
    
    missions = []
    for mission_type in MissionType:
        meta = MISSION_METADATA.get(mission_type, {})
        existing = existing_missions.get(mission_type)
        
        missions.append(MissionResponse(
            mission_type=mission_type.value,
            name=meta.get("name", "Unknown"),
            description=meta.get("description", ""),
            points=meta.get("points", 0),
            completed=existing.completed if existing else False,
            completed_at=existing.completed_at if existing else None
        ))
    
    return missions


@router.post("/missions/{mission_type}/complete")
async def complete_mission(
    mission_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a daily mission as complete"""
    try:
        mt = MissionType(mission_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mission type")
    
    today = utc_date_today()
    
    # Check if already completed
    result = await db.execute(
        select(DailyMission)
        .where(
            and_(
                DailyMission.user_id == current_user.id,
                DailyMission.mission_type == mt,
                DailyMission.mission_date >= today
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing and existing.completed:
        return {
            "status": "already_completed",
            "points_earned": 0
        }
    
    points = MISSION_METADATA.get(mt, {}).get("points", 0)
    
    if existing:
        existing.completed = True
        existing.completed_at = utcnow()
        existing.points_earned = points
    else:
        mission = DailyMission(
            user_id=current_user.id,
            mission_type=mt,
            mission_date=today,
            completed=True,
            completed_at=utcnow(),
            points_earned=points
        )
        db.add(mission)
    
    # Award points
    current_user.k_points += points
    
    await db.commit()
    
    return {
        "status": "completed",
        "mission_type": mission_type,
        "points_earned": points,
        "total_k_points": current_user.k_points
    }


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get top creators by royalty earned"""
    # Get top users by total_royalty_received
    result = await db.execute(
        select(User)
        .where(User.total_royalty_received > 0)
        .order_by(User.total_royalty_received.desc())
        .limit(limit)
    )
    users = result.scalars().all()
    
    entries = []
    for rank, user in enumerate(users, 1):
        # Get badge count
        badge_result = await db.execute(
            select(func.count(UserBadge.id))
            .where(UserBadge.user_id == user.id)
        )
        badge_count = badge_result.scalar() or 0
        
        # Get streak
        streak_result = await db.execute(
            select(UserStreak).where(UserStreak.user_id == user.id)
        )
        streak = streak_result.scalar_one_or_none()
        streak_days = streak.current_streak if streak else 0
        
        entries.append(LeaderboardEntry(
            rank=rank,
            user_id=str(user.id),
            user_name=user.name,
            profile_image=user.profile_image,
            total_royalty=user.total_royalty_received,
            streak_days=streak_days,
            badge_count=badge_count
        ))
    
    return entries
