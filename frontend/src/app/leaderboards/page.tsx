"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, GamificationLeaderboardEntry, Badge, StreakInfo, DailyMission } from "@/lib/api";
import { AppHeader } from "@/components/AppHeader";

export default function LeaderboardPage() {
    const [leaderboard, setLeaderboard] = useState<GamificationLeaderboardEntry[]>([]);
    const [myBadges, setMyBadges] = useState<Badge[]>([]);
    const [myStreak, setMyStreak] = useState<StreakInfo | null>(null);
    const [dailyMissions, setDailyMissions] = useState<DailyMission[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        try {
            const [leaderboardData, badgesData, streakData, missionsData] = await Promise.all([
                api.getGamificationLeaderboard(10),
                api.getMyBadges().catch(() => []),
                api.getMyStreak().catch(() => null),
                api.getDailyMissions().catch(() => []),
            ]);
            setLeaderboard(leaderboardData);
            setMyBadges(badgesData);
            setMyStreak(streakData);
            setDailyMissions(missionsData);
        } catch (err) {
            console.error("Failed to load leaderboard:", err);
        } finally {
            setLoading(false);
        }
    }

    async function handleCompleteMission(missionType: string) {
        try {
            await api.completeMission(missionType);
            await loadData();
        } catch (err) {
            console.error("Failed to complete mission:", err);
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-white/50">리더보드 로딩 중...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white pb-20">
            {/* Aurora Background */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-violet-600/20 blur-[150px] rounded-full" />
                <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-pink-600/15 blur-[150px] rounded-full" />
            </div>

            <AppHeader />

            <main className="relative z-10 max-w-6xl mx-auto px-6 pt-24">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-5xl font-black mb-4 tracking-tight">
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-orange-400 to-pink-400">
                            🏆 리더보드
                        </span>
                    </h1>
                    <p className="text-xl text-white/40">
                        K-MEME 크리에이터 TOP 10
                    </p>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Leaderboard Column */}
                    <div className="lg:col-span-2 space-y-4">
                        <h2 className="text-xl font-bold flex items-center gap-2 mb-4">
                            <span className="text-2xl">👑</span> 주간 수익 TOP 10
                        </h2>
                        {leaderboard.map((entry, idx) => (
                            <div
                                key={entry.user_id}
                                className={`p-4 rounded-2xl border transition-all ${idx === 0
                                        ? "bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border-yellow-500/30"
                                        : idx === 1
                                            ? "bg-gradient-to-r from-slate-400/10 to-slate-300/10 border-slate-400/30"
                                            : idx === 2
                                                ? "bg-gradient-to-r from-amber-700/10 to-amber-600/10 border-amber-600/30"
                                                : "bg-white/5 border-white/10"
                                    }`}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        {/* Rank */}
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-black text-lg ${idx === 0 ? "bg-yellow-500 text-black" :
                                                idx === 1 ? "bg-slate-400 text-black" :
                                                    idx === 2 ? "bg-amber-600 text-white" :
                                                        "bg-white/10 text-white/50"
                                            }`}>
                                            {entry.rank}
                                        </div>
                                        {/* Profile */}
                                        <div className="flex items-center gap-3">
                                            {entry.profile_image ? (
                                                <img
                                                    src={entry.profile_image}
                                                    alt=""
                                                    className="w-10 h-10 rounded-full"
                                                />
                                            ) : (
                                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-pink-500" />
                                            )}
                                            <div>
                                                <div className="font-bold text-white">
                                                    {entry.user_name || "Anonymous"}
                                                </div>
                                                <div className="flex items-center gap-2 text-xs text-white/40">
                                                    <span>🔥 {entry.streak_days}일</span>
                                                    <span>🏅 {entry.badge_count}개</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    {/* Total Royalty */}
                                    <div className="text-right">
                                        <div className="text-xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-400">
                                            {entry.total_royalty.toLocaleString()} P
                                        </div>
                                        <div className="text-xs text-white/40">누적 로열티</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                        {leaderboard.length === 0 && (
                            <div className="text-center py-12 text-white/40">
                                아직 리더보드 데이터가 없습니다.
                            </div>
                        )}
                    </div>

                    {/* Sidebar - My Stats & Missions */}
                    <div className="space-y-6">
                        {/* My Streak */}
                        {myStreak && (
                            <div className="glass-panel p-6 rounded-2xl border border-orange-500/20">
                                <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                                    <span className="text-xl">🔥</span> 내 스트릭
                                </h3>
                                <div className="text-center">
                                    <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-500 mb-2">
                                        {myStreak.current_streak}일
                                    </div>
                                    <p className="text-white/40 text-sm">
                                        {myStreak.next_milestone > 0
                                            ? `다음 보상까지 ${myStreak.next_milestone}일`
                                            : "최대 스트릭 달성! 🎉"
                                        }
                                    </p>
                                </div>
                                <div className="mt-4 pt-4 border-t border-white/10 flex justify-between text-sm">
                                    <span className="text-white/40">최고 기록</span>
                                    <span className="text-white font-bold">{myStreak.longest_streak}일</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-white/40">스트릭 포인트</span>
                                    <span className="text-orange-400 font-bold">+{myStreak.streak_points_earned}P</span>
                                </div>
                            </div>
                        )}

                        {/* My Badges */}
                        <div className="glass-panel p-6 rounded-2xl border border-violet-500/20">
                            <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                                <span className="text-xl">🏅</span> 내 뱃지
                            </h3>
                            {myBadges.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                    {myBadges.map((badge, idx) => (
                                        <div
                                            key={idx}
                                            className="px-3 py-2 bg-white/5 rounded-xl border border-white/10 text-center"
                                            title={badge.description}
                                        >
                                            <div className="text-xl">{badge.emoji}</div>
                                            <div className="text-[10px] text-white/50">{badge.name}</div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-white/40 text-sm text-center py-4">
                                    아직 획득한 뱃지가 없어요.<br />리믹스를 시작해보세요!
                                </p>
                            )}
                        </div>

                        {/* Daily Missions */}
                        <div className="glass-panel p-6 rounded-2xl border border-emerald-500/20">
                            <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                                <span className="text-xl">📋</span> 오늘의 미션
                            </h3>
                            <div className="space-y-3">
                                {dailyMissions.map((mission) => (
                                    <div
                                        key={mission.mission_type}
                                        className={`p-3 rounded-xl flex items-center justify-between ${mission.completed
                                                ? "bg-emerald-500/10 border border-emerald-500/30"
                                                : "bg-white/5 border border-white/10"
                                            }`}
                                    >
                                        <div>
                                            <div className="font-bold text-white text-sm">{mission.name}</div>
                                            <div className="text-xs text-white/40">{mission.description}</div>
                                        </div>
                                        {mission.completed ? (
                                            <span className="text-emerald-400 text-sm">✅</span>
                                        ) : (
                                            <span className="text-yellow-400 font-bold text-sm">+{mission.points}P</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* CTA */}
                        <Link
                            href="/"
                            className="block w-full py-4 rounded-2xl bg-gradient-to-r from-violet-500 to-pink-500 text-white font-bold text-center hover:from-violet-400 hover:to-pink-400 transition-all shadow-[0_0_30px_rgba(139,92,246,0.3)]"
                        >
                            🚀 리믹스 시작하기
                        </Link>
                    </div>
                </div>
            </main>
        </div>
    );
}
