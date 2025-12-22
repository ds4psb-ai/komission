"use client";

import React from 'react';

interface RoyaltyBadgeProps {
    /** Total points earned from this node */
    totalRoyalty: number;
    /** Number of times this node has been forked */
    forkCount: number;
    /** Size variant */
    size?: 'sm' | 'md' | 'lg';
    /** Show detailed breakdown */
    showDetails?: boolean;
}

/**
 * RoyaltyBadge - Displays royalty earnings for a node or user
 * Shows K-Points earned and fork count with visual flair
 */
export function RoyaltyBadge({
    totalRoyalty,
    forkCount,
    size = 'md',
    showDetails = false
}: RoyaltyBadgeProps) {
    const sizeClasses = {
        sm: 'text-xs px-2 py-1',
        md: 'text-sm px-3 py-1.5',
        lg: 'text-base px-4 py-2'
    };

    const iconSize = {
        sm: 'text-sm',
        md: 'text-base',
        lg: 'text-lg'
    };

    // Format large numbers
    const formatNumber = (num: number): string => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    };

    // Determine badge glow based on royalty tier
    const getGlowClass = (royalty: number): string => {
        if (royalty >= 10000) return 'shadow-[0_0_20px_rgba(250,204,21,0.5)]'; // Gold
        if (royalty >= 1000) return 'shadow-[0_0_15px_rgba(168,85,247,0.4)]';  // Purple
        if (royalty >= 100) return 'shadow-[0_0_10px_rgba(59,130,246,0.3)]';   // Blue
        return '';
    };

    // Determine badge color based on royalty tier
    const getBadgeColor = (royalty: number): string => {
        if (royalty >= 10000) return 'from-yellow-500/20 to-amber-600/20 border-yellow-500/40';
        if (royalty >= 1000) return 'from-purple-500/20 to-violet-600/20 border-purple-500/40';
        if (royalty >= 100) return 'from-blue-500/20 to-cyan-600/20 border-blue-500/40';
        return 'from-white/5 to-white/10 border-white/20';
    };

    if (!showDetails) {
        // Compact badge for node cards
        return (
            <div className={`
                inline-flex items-center gap-1.5 rounded-full
                bg-gradient-to-r ${getBadgeColor(totalRoyalty)}
                border backdrop-blur-sm
                ${sizeClasses[size]}
                ${getGlowClass(totalRoyalty)}
                transition-all duration-300 hover:scale-105
            `}>
                <span className={`${iconSize[size]}`}>💰</span>
                <span className="font-bold text-white/90">
                    +{formatNumber(totalRoyalty)}
                </span>
                {forkCount > 0 && (
                    <>
                        <span className="text-white/30">|</span>
                        <span className="text-white/60">
                            🔀 {formatNumber(forkCount)}
                        </span>
                    </>
                )}
            </div>
        );
    }

    // Detailed breakdown for dashboards
    return (
        <div className={`
            rounded-xl bg-gradient-to-br ${getBadgeColor(totalRoyalty)}
            border backdrop-blur-md p-4
            ${getGlowClass(totalRoyalty)}
        `}>
            <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-bold text-white/60 uppercase tracking-wider">
                    Creator Royalty
                </h4>
                <span className="text-2xl">💰</span>
            </div>

            <div className="text-3xl font-black text-white mb-1">
                {formatNumber(totalRoyalty)} <span className="text-lg font-normal text-white/50">K-Points</span>
            </div>

            <div className="flex items-center gap-4 text-sm text-white/60">
                <div className="flex items-center gap-1">
                    <span>🔀</span>
                    <span>{formatNumber(forkCount)} Forks</span>
                </div>
                <div className="flex items-center gap-1">
                    <span>📈</span>
                    <span>{forkCount > 0 ? Math.round(totalRoyalty / forkCount) : 0} avg/fork</span>
                </div>
            </div>
        </div>
    );
}

interface RoyaltyHistoryItemProps {
    points: number;
    reason: 'fork' | 'view_milestone' | 'k_success' | 'genealogy_bonus';
    createdAt: string;
    nodeTitle?: string;
}

/**
 * RoyaltyHistoryItem - Single row in royalty transaction history
 */
export function RoyaltyHistoryItem({
    points,
    reason,
    createdAt,
    nodeTitle
}: RoyaltyHistoryItemProps) {
    const reasonConfig = {
        fork: { icon: '🔀', label: 'Node Forked', color: 'text-blue-400' },
        view_milestone: { icon: '👀', label: 'View Milestone', color: 'text-green-400' },
        k_success: { icon: '🏆', label: 'K-Success', color: 'text-yellow-400' },
        genealogy_bonus: { icon: '🌳', label: 'Genealogy Bonus', color: 'text-purple-400' },
    };

    const config = reasonConfig[reason] || reasonConfig.fork;

    const formatDate = (dateStr: string): string => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
            <div className="flex items-center gap-3">
                <span className="text-xl">{config.icon}</span>
                <div>
                    <div className={`font-medium ${config.color}`}>
                        {config.label}
                    </div>
                    {nodeTitle && (
                        <div className="text-xs text-white/40 truncate max-w-[200px]">
                            {nodeTitle}
                        </div>
                    )}
                </div>
            </div>

            <div className="text-right">
                <div className="font-bold text-green-400">
                    +{points}
                </div>
                <div className="text-xs text-white/40">
                    {formatDate(createdAt)}
                </div>
            </div>
        </div>
    );
}

interface CreatorLeaderboardEntryProps {
    rank: number;
    userName: string | null;
    totalRoyalty: number;
    nodeCount: number;
}

/**
 * CreatorLeaderboardEntry - Single row in creator leaderboard
 */
export function CreatorLeaderboardEntry({
    rank,
    userName,
    totalRoyalty,
    nodeCount
}: CreatorLeaderboardEntryProps) {
    const getRankStyle = (r: number) => {
        if (r === 1) return 'bg-gradient-to-r from-yellow-500 to-amber-500 text-black';
        if (r === 2) return 'bg-gradient-to-r from-slate-400 to-slate-300 text-black';
        if (r === 3) return 'bg-gradient-to-r from-amber-700 to-amber-600 text-white';
        return 'bg-white/10 text-white/60';
    };

    return (
        <div className="flex items-center gap-4 py-3 px-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
            <div className={`
                w-8 h-8 rounded-full flex items-center justify-center 
                font-black text-sm ${getRankStyle(rank)}
            `}>
                {rank}
            </div>

            <div className="flex-1">
                <div className="font-medium text-white">
                    {userName || 'Anonymous Creator'}
                </div>
                <div className="text-xs text-white/40">
                    {nodeCount} nodes
                </div>
            </div>

            <div className="text-right">
                <div className="font-bold text-yellow-400">
                    {totalRoyalty.toLocaleString()}
                </div>
                <div className="text-xs text-white/40">K-Points</div>
            </div>
        </div>
    );
}
