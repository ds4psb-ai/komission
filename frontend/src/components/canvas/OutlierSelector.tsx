"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { api, RemixNode } from '@/lib/api';

interface OutlierSelectorProps {
    onSelect: (node: RemixNode) => void;
    onClose: () => void;
}

type LoadingState = 'loading' | 'success' | 'error' | 'empty';

export function OutlierSelector({ onSelect, onClose }: OutlierSelectorProps) {
    const [nodes, setNodes] = useState<RemixNode[]>([]);
    const [loadingState, setLoadingState] = useState<LoadingState>('loading');
    const [errorMessage, setErrorMessage] = useState<string>('');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

    const loadNodes = useCallback(async () => {
        setLoadingState('loading');
        setErrorMessage('');
        try {
            // FIXED: Use correct API signature with object params
            const result = await api.listRemixNodes({
                limit: 50,
                layer: 'master'  // Only show master nodes (viral sources)
            });

            if (!result || result.length === 0) {
                setLoadingState('empty');
                setNodes([]);
            } else {
                setNodes(result);
                setLoadingState('success');
            }
        } catch (e) {
            console.error('Failed to load outliers:', e);
            setLoadingState('error');
            setErrorMessage(e instanceof Error ? e.message : '노드 로딩에 실패했습니다');
        }
    }, []);

    useEffect(() => {
        loadNodes();
    }, [loadNodes]);

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

    // Filter nodes by search term and platform
    const filteredNodes = nodes.filter(n => {
        const matchesSearch = n.title.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesPlatform = !selectedPlatform || n.platform === selectedPlatform;
        return matchesSearch && matchesPlatform;
    });

    // Platform tabs
    const platforms = [
        { id: null, label: '전체', icon: '🌐' },
        { id: 'tiktok', label: 'TikTok', icon: '🎵' },
        { id: 'instagram', label: 'Reels', icon: '📷' },
        { id: 'youtube', label: 'Shorts', icon: '▶️' },
    ];

    return (
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={(e) => e.target === e.currentTarget && onClose()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="outlier-selector-title"
        >
            <div className="bg-[#1a1a1a] border border-white/10 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="p-6 border-b border-white/5 flex justify-between items-center bg-black/40">
                    <div>
                        <h2 id="outlier-selector-title" className="text-xl font-bold text-white flex items-center gap-2">
                            <span className="text-2xl">🧬</span> Outlier Node 선택
                        </h2>
                        <p className="text-xs text-white/40 mt-1">바이럴 히트에서 리믹스를 시작하세요</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-white/40 hover:text-white text-2xl transition-colors w-10 h-10 flex items-center justify-center rounded-lg hover:bg-white/10"
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>

                {/* Platform Filter Tabs */}
                <div className="px-4 py-3 border-b border-white/5 flex gap-2 bg-black/20 overflow-x-auto">
                    {platforms.map((p) => (
                        <button
                            key={p.id || 'all'}
                            onClick={() => setSelectedPlatform(p.id)}
                            className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap ${selectedPlatform === p.id
                                ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                                : 'bg-white/5 text-white/50 border border-transparent hover:bg-white/10 hover:text-white/80'
                                }`}
                        >
                            <span>{p.icon}</span>
                            {p.label}
                        </button>
                    ))}
                </div>

                {/* Search */}
                <div className="p-4 border-b border-white/5 bg-white/5">
                    <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30">🔍</span>
                        <input
                            type="text"
                            placeholder="노드 검색..."
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
                            <p className="text-sm">바이럴 노드 로딩중...</p>
                        </div>
                    )}

                    {/* Error State */}
                    {loadingState === 'error' && (
                        <div className="flex flex-col items-center justify-center py-20 text-center">
                            <div className="text-5xl mb-4 opacity-50">⚠️</div>
                            <h3 className="text-lg font-bold text-white mb-2">로딩 실패</h3>
                            <p className="text-sm text-white/40 mb-6 max-w-sm">{errorMessage || '네트워크 오류가 발생했습니다'}</p>
                            <button
                                onClick={loadNodes}
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
                            <h3 className="text-lg font-bold text-white mb-2">Outlier 노드 없음</h3>
                            <p className="text-sm text-white/40 max-w-sm">
                                아직 등록된 바이럴 노드가 없습니다.<br />
                                관리자가 마스터 노드를 추가할 때까지 기다려주세요.
                            </p>
                        </div>
                    )}

                    {/* Success State - Grid */}
                    {loadingState === 'success' && (
                        <>
                            {filteredNodes.length === 0 ? (
                                <div className="text-center py-20 text-white/30">
                                    <div className="text-4xl mb-4 opacity-30">🔍</div>
                                    <p>"{searchTerm}"에 해당하는 노드가 없습니다</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                    {filteredNodes.map(node => (
                                        <button
                                            key={node.id}
                                            onClick={() => onSelect(node)}
                                            className="group relative aspect-square bg-black border border-white/10 rounded-xl overflow-hidden cursor-pointer hover:border-violet-500/50 transition-all hover:shadow-[0_0_20px_rgba(139,92,246,0.15)] text-left"
                                        >
                                            {/* Gradient Background */}
                                            <div className={`absolute inset-0 bg-gradient-to-br ${node.platform === 'tiktok' ? 'from-pink-600/30 to-cyan-600/20' :
                                                node.platform === 'instagram' ? 'from-purple-600/30 to-orange-600/20' :
                                                    'from-red-600/30 to-gray-600/20'
                                                } opacity-60`} />

                                            {/* Platform Icon */}
                                            <div className="absolute top-3 left-3 z-10 w-7 h-7 rounded-full bg-black/60 backdrop-blur flex items-center justify-center border border-white/10 text-sm">
                                                {node.platform === 'tiktok' ? '🎵' : node.platform === 'instagram' ? '📷' : '▶️'}
                                            </div>

                                            {/* Stats */}
                                            <div className="absolute top-3 right-3 z-10 px-2 py-1 rounded-full bg-black/60 backdrop-blur border border-white/10 text-[10px] text-white flex items-center gap-1 font-mono">
                                                👁️ {(node.view_count / 10000).toFixed(1)}만
                                            </div>

                                            {/* Performance Delta Badge */}
                                            {node.performance_delta && (
                                                <div className="absolute top-12 right-3 z-10 px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30 text-[9px] text-emerald-400 font-bold">
                                                    {node.performance_delta}
                                                </div>
                                            )}

                                            {/* Gradient Overlay */}
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />

                                            {/* Content */}
                                            <div className="absolute bottom-0 left-0 right-0 p-4">
                                                <div className="text-sm font-bold text-white line-clamp-2 group-hover:text-violet-300 transition-colors mb-1.5">
                                                    {node.title}
                                                </div>
                                                <div className="text-[10px] text-white/40 flex items-center gap-2">
                                                    <span className="px-1.5 py-0.5 bg-white/10 rounded text-white/60">
                                                        레이어 {node.genealogy_depth + 1}
                                                    </span>
                                                    <span>•</span>
                                                    <span>{new Date(node.created_at).toLocaleDateString('ko-KR')}</span>
                                                </div>
                                            </div>

                                            {/* Hover Highlight */}
                                            <div className="absolute inset-0 border-2 border-violet-500 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl pointer-events-none" />

                                            {/* Selection Indicator */}
                                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all">
                                                <div className="w-12 h-12 rounded-full bg-violet-500/80 flex items-center justify-center shadow-lg backdrop-blur">
                                                    <span className="text-xl">✓</span>
                                                </div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/5 bg-black/40 flex justify-between items-center">
                    <span className="text-xs text-white/30">
                        {loadingState === 'success' && `${filteredNodes.length}개의 노드`}
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
