"use client";

import React, { useEffect, useState } from 'react';
import { AppHeader } from '@/components/AppHeader';
import { api, Pipeline } from '@/lib/api';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

// Skeleton Card Component
function SkeletonCard() {
    return (
        <div className="bg-[#111] border border-white/10 rounded-2xl overflow-hidden animate-pulse">
            <div className="h-40 bg-white/5" />
            <div className="p-6 space-y-3">
                <div className="h-6 bg-white/10 rounded w-3/4" />
                <div className="h-4 bg-white/5 rounded w-1/2" />
                <div className="h-10 bg-white/5 rounded-xl mt-6" />
            </div>
        </div>
    );
}

export default function PipelineMarketplacePage() {
    const router = useRouter();
    const [pipelines, setPipelines] = useState<Pipeline[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadPipelines();
    }, []);

    const loadPipelines = async () => {
        try {
            setError(null);
            const list = await api.listPublicPipelines();
            setPipelines(list);
        } catch (e) {
            console.warn('공개 파이프라인 로드 실패', e);
            setError('공개 파이프라인 로드 실패');
        } finally {
            setLoading(false);
        }
    };

    const handleUseTemplate = (pipelineId: string) => {
        router.push(`/canvas?templateId=${pipelineId}`);
    };

    return (
        <div className="min-h-screen bg-black text-white font-sans selection:bg-pink-500/30">
            <AppHeader />

            <main className="max-w-7xl mx-auto px-6 py-12">
                <div className="mb-12 text-center">
                    <h1 className="text-4xl md:text-6xl font-black bg-gradient-to-r from-violet-400 via-pink-400 to-orange-400 bg-clip-text text-transparent mb-4">
                        파이프라인 마켓
                    </h1>
                    <p className="text-white/60 text-lg max-w-2xl mx-auto">
                        Komission 커뮤니티의 검증된 바이럴 공식을 발견하고 리믹스하세요.
                    </p>
                </div>

                {/* Action Bar */}
                <div className="flex justify-between items-center mb-8">
                    <div className="text-sm text-white/40">
                        {!loading && !error && `${pipelines.length}개의 공개 워크플로우`}
                    </div>
                    <Link
                        href="/canvas"
                        className="px-4 py-2 bg-gradient-to-r from-violet-500 to-pink-500 rounded-xl font-bold text-sm hover:opacity-90 transition-opacity flex items-center gap-2"
                    >
                        ⚡ 새 파이프라인 만들기
                    </Link>
                </div>

                {/* Error State */}
                {error && (
                    <div className="text-center py-12 bg-red-500/10 rounded-3xl border border-red-500/20">
                        <p className="text-red-400 text-xl font-bold mb-4">{error}</p>
                        <button
                            onClick={() => { setLoading(true); loadPipelines(); }}
                            className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 rounded-lg text-red-400 text-sm font-bold transition-colors"
                        >
                            ↻ 다시 시도
                        </button>
                    </div>
                )}

                {/* Loading State - Skeleton */}
                {loading && !error && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <SkeletonCard key={i} />
                        ))}
                    </div>
                )}

                {/* Empty State */}
                {!loading && !error && pipelines.length === 0 && (
                    <div className="text-center py-20 bg-white/5 rounded-3xl border border-white/10">
                        <div className="text-6xl mb-6">🚀</div>
                        <p className="text-white/40 text-xl font-bold">아직 공개된 파이프라인이 없습니다.</p>
                        <p className="text-white/30 mt-2 mb-6">첫 번째로 워크플로우를 공유해보세요!</p>
                        <Link
                            href="/canvas"
                            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-violet-500 to-pink-500 rounded-xl font-bold hover:opacity-90 transition-opacity"
                        >
                            ⚡ 파이프라인 만들기
                        </Link>
                    </div>
                )}

                {/* Pipeline Grid */}
                {!loading && !error && pipelines.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {pipelines.map((p) => (
                            <div
                                key={p.id}
                                className="group relative bg-[#111] border border-white/10 hover:border-violet-500/50 rounded-2xl overflow-hidden transition-all hover:shadow-2xl hover:shadow-violet-900/20"
                            >
                                {/* Preview Area */}
                                <div className="h-40 bg-gradient-to-br from-violet-900/20 to-pink-900/20 flex items-center justify-center border-b border-white/5 relative">
                                    <span className="text-4xl">⚡</span>
                                    {/* Node count badge */}
                                    <div className="absolute bottom-2 right-2 text-xs bg-black/50 px-2 py-1 rounded text-white/50">
                                        {((p.graph_data?.nodes as unknown[]) || []).length}개 노드
                                    </div>
                                </div>

                                <div className="p-6">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="text-xl font-bold text-white group-hover:text-violet-400 transition-colors line-clamp-1">
                                            {p.title}
                                        </h3>
                                        <span className="text-xs font-mono bg-white/10 px-2 py-1 rounded text-white/60 shrink-0">
                                            v1.0
                                        </span>
                                    </div>
                                    <p className="text-white/40 text-sm mb-6">
                                        업데이트: {new Date(p.updated_at).toLocaleDateString()}
                                    </p>

                                    <button
                                        onClick={() => handleUseTemplate(p.id)}
                                        className="w-full py-3 bg-white/5 hover:bg-violet-500 border border-white/10 hover:border-violet-400 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 text-white/70 hover:text-white"
                                    >
                                        <span>🚀</span> 템플릿 사용하기
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
