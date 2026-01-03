"use client";
import { useTranslations } from 'next-intl';

import React, { useEffect, useState, useCallback, useRef } from 'react';

// Unified Outlier type - works for all outliers (DB + Crawled)
export interface OutlierItem {
    id: string;
    title: string;
    platform: string;
    video_url: string;
    thumbnail_url?: string;
    view_count?: number;
    tier?: string;
    outlier_tier?: string;
    source?: string;
    category?: string;
    created_at?: string;
    vdg_analysis?: any;
}

interface OutlierSelectorProps {
    onSelect: (item: OutlierItem) => void;
    onClose: () => void;
}

type LoadingState = 'loading' | 'success' | 'error' | 'empty';

export function OutlierSelector({ onSelect, onClose }: OutlierSelectorProps) {
    const [items, setItems] = useState<OutlierItem[]>([]);
    const [loadingState, setLoadingState] = useState<LoadingState>('loading');
    const [errorMessage, setErrorMessage] = useState<string>('');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
    const [selectedTier, setSelectedTier] = useState<string | null>(null);
    const isMountedRef = useRef(true);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const loadItems = useCallback(async () => {
        if (isMountedRef.current) {
            setLoadingState('loading');
            setErrorMessage('');
        }
        try {
            // Use unified outliers API
            const response = await fetch('/api/v1/outliers/?limit=100');
            if (!response.ok) throw new Error('Failed to fetch outliers');

            const data = await response.json();
            const outliers = data.items || data || [];

            if (!isMountedRef.current) return;
            if (!outliers || outliers.length === 0) {
                setLoadingState('empty');
                setItems([]);
            } else {
                setItems(outliers);
                setLoadingState('success');
            }
        } catch (e) {
            console.error('Failed to load outliers:', e);
            if (!isMountedRef.current) return;
            setLoadingState('error');
            setErrorMessage(e instanceof Error ? e.message : '로딩에 실패했습니다');
        }
    }, []);

    useEffect(() => {
        loadItems();
    }, [loadItems]);

    // Handle keyboard navigation
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onClose]);

    // Filter items
    const normalizedSearch = searchTerm.trim().toLowerCase();
    const filteredItems = items.filter(item => {
        const itemTier = item.tier ?? item.outlier_tier;
        const matchesSearch = !normalizedSearch
            || (item.title ?? '').toLowerCase().includes(normalizedSearch);
        const matchesPlatform = !selectedPlatform || item.platform === selectedPlatform;
        const matchesTier = !selectedTier || itemTier === selectedTier;
        return matchesSearch && matchesPlatform && matchesTier;
    });

    // Platform tabs
    const platforms = [
        { id: null, label: '전체', icon: '🌐' },
        { id: 'tiktok', label: 'TikTok', icon: '🎵' },
        { id: 'youtube', label: 'Shorts', icon: '▶️' },
        { id: 'instagram', label: 'Reels', icon: '📷' },
    ];

    // Tier filter
    const tiers = [
        { id: null, label: '전체' },
        { id: 'S', label: 'S티어', color: 'text-amber-400' },
        { id: 'A', label: 'A티어', color: 'text-violet-400' },
        { id: 'B', label: 'B티어', color: 'text-blue-400' },
    ];

    const getTierColor = (tier?: string) => {
        switch (tier) {
            case 'S': return 'from-amber-500/40 to-orange-500/40 border-amber-500/50';
            case 'A': return 'from-violet-500/40 to-purple-500/40 border-violet-500/50';
            case 'B': return 'from-blue-500/40 to-cyan-500/40 border-blue-500/50';
            default: return 'from-gray-500/40 to-gray-600/40 border-gray-500/50';
        }
    };

    const formatViews = (count?: number) => {
        if (typeof count !== 'number' || Number.isNaN(count)) return '—';
        if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
        if (count >= 1000) return `${(count / 1000).toFixed(0)}K`;
        return count.toString();
    };

    return (
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={(e) => e.target === e.currentTarget && onClose()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="outlier-selector-title"
        >
            <div className="bg-[#1a1a1a] border border-white/10 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="p-6 border-b border-white/5 flex justify-between items-center bg-black/40">
                    <div>
                        <h2 id="outlier-selector-title" className="text-xl font-bold text-white flex items-center gap-2">
                            <span className="text-2xl">🧬</span> 아웃라이어 선택
                        </h2>
                        <p className="text-xs text-white/40 mt-1">바이럴 히트 영상을 선택해서 캔버스에 추가하세요</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-white/40 hover:text-white text-2xl transition-colors w-10 h-10 flex items-center justify-center rounded-lg hover:bg-white/10"
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>

                {/* Filters Row */}
                <div className="px-4 py-3 border-b border-white/5 flex gap-4 bg-black/20 overflow-x-auto items-center">
                    {/* Platform Filter */}
                    <div className="flex gap-1.5">
                        {platforms.map((p) => (
                            <button
                                key={p.id || 'all'}
                                onClick={() => setSelectedPlatform(p.id)}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap ${selectedPlatform === p.id
                                    ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                                    : 'bg-white/5 text-white/50 border border-transparent hover:bg-white/10 hover:text-white/80'
                                    }`}
                            >
                                <span>{p.icon}</span>
                                {p.label}
                            </button>
                        ))}
                    </div>

                    <div className="w-px h-6 bg-white/10" />

                    {/* Tier Filter */}
                    <div className="flex gap-1.5">
                        {tiers.map((t) => (
                            <button
                                key={t.id || 'all'}
                                onClick={() => setSelectedTier(t.id)}
                                className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all ${selectedTier === t.id
                                    ? `bg-white/20 ${t.color || 'text-white'}`
                                    : 'bg-white/5 text-white/50 hover:bg-white/10'
                                    }`}
                            >
                                {t.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Search */}
                <div className="p-4 border-b border-white/5 bg-white/5">
                    <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30">🔍</span>
                        <input
                            type="text"
                            placeholder="아웃라이어 검색..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-black/40 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-sm text-white focus:outline-none focus:border-violet-500/50 transition-all placeholder-white/20"
                            autoFocus
                        />
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                    {/* Loading State */}
                    {loadingState === 'loading' && (
                        <div className="flex flex-col items-center justify-center py-20 text-white/30 gap-4">
                            <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
                            <p className="text-sm">아웃라이어 로딩중...</p>
                        </div>
                    )}

                    {/* Error State */}
                    {loadingState === 'error' && (
                        <div className="flex flex-col items-center justify-center py-20 text-center">
                            <div className="text-5xl mb-4 opacity-50">⚠️</div>
                            <h3 className="text-lg font-bold text-white mb-2">로딩 실패</h3>
                            <p className="text-sm text-white/40 mb-6 max-w-sm">{errorMessage || '네트워크 오류가 발생했습니다'}</p>
                            <button
                                onClick={loadItems}
                                className="px-6 py-2.5 bg-violet-500/20 hover:bg-violet-500/30 text-violet-300 border border-violet-500/30 rounded-xl text-sm font-bold transition-all"
                            >
                                🔄 다시 시도
                            </button>
                        </div>
                    )}

                    {/* Empty State */}
                    {loadingState === 'empty' && (
                        <div className="flex flex-col items-center justify-center py-20 text-center">
                            <div className="text-5xl mb-4 opacity-30">📡</div>
                            <h3 className="text-lg font-bold text-white mb-2">아웃라이어 없음</h3>
                            <p className="text-sm text-white/40 max-w-sm">
                                아직 등록된 아웃라이어가 없습니다.<br />
                                크롤러가 수집하면 여기에 표시됩니다.
                            </p>
                        </div>
                    )}

                    {/* Success State - Grid */}
                    {loadingState === 'success' && (
                        <>
                            {filteredItems.length === 0 ? (
                                <div className="text-center py-20 text-white/30">
                                    <div className="text-4xl mb-4 opacity-30">🔍</div>
                                    <p>"{searchTerm}"에 해당하는 아웃라이어가 없습니다</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                                    {filteredItems.map(item => {
                                        const itemTier = item.tier ?? item.outlier_tier;
                                        return (
                                            <button
                                                key={item.id}
                                                onClick={() => onSelect(item)}
                                                className="group relative aspect-[9/16] bg-black border border-white/10 rounded-xl overflow-hidden cursor-pointer hover:border-violet-500/50 transition-all hover:shadow-[0_0_20px_rgba(139,92,246,0.15)] text-left"
                                            >
                                            {/* Thumbnail */}
                                            {item.thumbnail_url ? (
                                                <img
                                                    src={item.thumbnail_url}
                                                    alt={item.title || 'Outlier thumbnail'}
                                                    className="absolute inset-0 w-full h-full object-cover"
                                                />
                                            ) : (
                                                <div className={`absolute inset-0 bg-gradient-to-br ${getTierColor(itemTier)}`} />
                                            )}

                                            {/* Tier Badge */}
                                            {itemTier && (
                                                <div className={`absolute top-2 left-2 z-10 w-7 h-7 rounded-lg flex items-center justify-center font-black text-sm
                                                    ${itemTier === 'S' ? 'bg-gradient-to-br from-amber-400 to-orange-500 text-black shadow-[0_0_12px_rgba(251,191,36,0.6)]' :
                                                        itemTier === 'A' ? 'bg-gradient-to-br from-violet-400 to-purple-500 text-white shadow-[0_0_12px_rgba(139,92,246,0.6)]' :
                                                            itemTier === 'B' ? 'bg-gradient-to-br from-blue-400 to-cyan-500 text-white shadow-[0_0_12px_rgba(59,130,246,0.6)]' :
                                                                'bg-white/20 text-white/60'}`}
                                                >
                                                    {itemTier}
                                                </div>
                                            )}

                                            {/* Platform Icon */}
                                            <div className="absolute top-2 right-2 z-10 w-6 h-6 rounded-full bg-black/60 backdrop-blur flex items-center justify-center text-xs">
                                                {item.platform === 'tiktok' ? '🎵' : item.platform === 'instagram' ? '📷' : '▶️'}
                                            </div>

                                            {/* Views */}
                                            <div className="absolute top-9 right-2 z-10 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur text-[10px] text-white/80 font-mono">
                                                {formatViews(item.view_count)}
                                            </div>

                                            {/* Gradient Overlay */}
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />

                                            {/* Content */}
                                            <div className="absolute bottom-0 left-0 right-0 p-3">
                                                <div className="text-xs font-bold text-white line-clamp-2 group-hover:text-violet-300 transition-colors">
                                                    {item.title || 'Untitled'}
                                                </div>
                                                {item.category && (
                                                    <div className="text-[10px] text-white/40 mt-1">
                                                        {item.category}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Hover Highlight */}
                                            <div className="absolute inset-0 border-2 border-violet-500 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl pointer-events-none" />

                                            {/* Selection Indicator */}
                                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all">
                                                <div className="w-10 h-10 rounded-full bg-violet-500/80 flex items-center justify-center shadow-lg backdrop-blur">
                                                    <span className="text-lg">✓</span>
                                                </div>
                                            </div>
                                        </button>
                                        );
                                    })}
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/5 bg-black/40 flex justify-between items-center">
                    <span className="text-xs text-white/30">
                        {loadingState === 'success' && `${filteredItems.length}개의 아웃라이어`}
                    </span>
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-white/60 hover:text-white transition-all"
                    >
                        취소
                    </button>
                </div>
            </div>
        </div>
    );
}
