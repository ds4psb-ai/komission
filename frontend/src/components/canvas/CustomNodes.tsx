import { useTranslations } from 'next-intl';
import { memo, useEffect, useRef, useState } from 'react';
import { Handle, Position } from '@xyflow/react';
import { useRouter } from 'next/navigation';
import { RemixNode } from '@/lib/api';
import { Eye, Zap, Star, Award, Diamond, BarChart, ExternalLink, Camera, Rocket } from 'lucide-react';
import { NodeWrapper } from './NodeWrapper';
import { HANDLE_STYLES, formatViewCount } from './utils';
import { TierBadge, OutlierMetrics } from '@/components/outlier';

/**
 * CrawlerOutlierItem interface for 3-platform crawler data
 */
export interface CrawlerOutlierItem {
    id: string;
    external_id: string;
    video_url: string;
    platform: 'tiktok' | 'youtube' | 'instagram';
    category: string;
    title: string;
    thumbnail_url?: string;
    view_count: number;
    like_count?: number;
    outlier_score: number;
    outlier_tier: 'S' | 'A' | 'B' | 'C' | null;
    creator_avg_views: number;
    engagement_rate: number;
    crawled_at: string;
    status: 'pending' | 'selected' | 'rejected' | 'promoted';
}


interface SourceNodeData {
    url?: string;
    platform?: string;
    nodeId?: string;
    outlier?: RemixNode; // For selected outliers
    onUrlChange?: (url: string) => void;
    onSubmit?: (url: string, title: string) => Promise<void>;
    // Expert Recommendation: Governance Lock
    isLocked?: boolean;
    viralBadge?: string;
}

export const SourceNode = memo(({ data }: { data: SourceNodeData }) => {
    const [url, setUrl] = useState(data.url || '');
    const [title, setTitle] = useState('');
    const [loading, setLoading] = useState(false);
    const [verified, setVerified] = useState(!!data.platform || !!data.outlier);
    const isMountedRef = useRef(true);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    useEffect(() => {
        setUrl(data.url || '');
    }, [data.url]);

    useEffect(() => {
        setVerified(!!data.platform || !!data.outlier);
    }, [data.platform, data.outlier]);

    // If it's an outlier node, it's already verified
    if (data.outlier) {
        return (
            <NodeWrapper
                title={data.isLocked ? "🔒 브랜드 소스" : "소스: 아웃라이어"}
                colorClass={data.isLocked ? "border-amber-500/40" : "border-emerald-500/40"}
                status="done"
                isLocked={data.isLocked}
                viralBadge={data.viralBadge || `Layer ${(data.outlier.genealogy_depth ?? 0) + 1}`}
            >
                <div className="space-y-4">
                    <div className="aspect-video bg-black/60 rounded-xl overflow-hidden border border-white/10 relative group">
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex items-end p-4">
                            <div>
                                <div className="text-[10px] text-emerald-400 font-bold mb-1 flex items-center gap-1">
                                    {data.outlier.platform === 'tiktok' ? '🎵 TikTok' : '📷 Instagram'} 출처
                                </div>
                                <div className="text-sm font-bold text-white leading-tight line-clamp-2">
                                    {data.outlier.title}
                                </div>
                            </div>
                        </div>
                        <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur rounded text-[10px] font-mono border border-white/10">
                            👁️ {data.outlier.view_count.toLocaleString()}
                        </div>
                        {/* Play Overlay */}
                        <a
                            href={data.outlier.source_video_url || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur flex items-center justify-center transition-all transform hover:scale-110">
                                <span className="text-xl">▶️</span>
                            </div>
                        </a>
                    </div>

                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                        <div className="text-[10px] text-emerald-400 font-bold mb-1">리믹스 준비 완료</div>
                        <div className="text-xs text-white/60 leading-relaxed">
                            이 노드는 소스로 잠겨있습니다. 파이프라인이 이 버전에서 포크됩니다.
                        </div>
                    </div>
                </div>
                <Handle type="source" position={Position.Right} className={HANDLE_STYLES.emerald} />
            </NodeWrapper>
        );
    }

    const handleSubmit = async () => {
        if (!url || !data.onSubmit) return;
        if (isMountedRef.current) {
            setLoading(true);
        }
        try {
            await data.onSubmit(url, title || 'New Source');
            if (!isMountedRef.current) return;
            setVerified(true);
        } catch (e) {
            console.error(e);
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    };

    return (
        <NodeWrapper title="소스 미디어" colorClass="border-emerald-500/40" status={verified ? 'done' : loading ? 'running' : 'idle'}>
            <div className="space-y-4">
                <div>
                    <div className="text-[10px] text-white/40 uppercase font-bold tracking-widest mb-1.5">제목</div>
                    <input
                        className="bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white w-full focus:outline-none focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/20 transition-all placeholder-white/20"
                        placeholder="레시피 제목..."
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                    />
                </div>
                <div>
                    <div className="text-[10px] text-white/40 uppercase font-bold tracking-widest mb-1.5">Video URL</div>
                    <input
                        className="bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white w-full focus:outline-none focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/20 transition-all placeholder-white/20"
                        placeholder="TikTok/Reels URL..."
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                    />
                </div>

                {verified ? (
                    <div className="flex items-center gap-2 mt-2 px-3 py-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                        <span className="text-xl filter drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]">
                            {data.platform === 'tiktok' ? '🎵' : '📷'}
                        </span>
                        <span className="text-xs font-bold text-emerald-400">✓ 소스 등록됨</span>
                    </div>
                ) : (
                    <button
                        onClick={handleSubmit}
                        disabled={loading || !url}
                        className="w-full py-2.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 disabled:from-emerald-900 disabled:to-emerald-900 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:shadow-[0_0_25px_rgba(16,185,129,0.4)] flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                <span>Registering...</span>
                            </>
                        ) : (
                            <span>📥 소스 등록</span>
                        )}
                    </button>
                )}
            </div>
            <Handle type="source" position={Position.Right} className="!bg-emerald-500 !w-3 !h-3 !border-2 !border-black" />
        </NodeWrapper>
    );
});

SourceNode.displayName = 'SourceNode';

interface ProcessNodeData {
    nodeId?: string;
    status?: 'idle' | 'running' | 'done' | 'error';
    logs?: string[];
    onAnalyze?: (nodeId: string) => Promise<void>;
}

export const ProcessNode = memo(({ data }: { data: ProcessNodeData }) => {
    const [running, setRunning] = useState(false);
    const [logs, setLogs] = useState<string[]>(data.logs || ['> 입력 대기 중...']);
    const [done, setDone] = useState(data.status === 'done');
    const isMountedRef = useRef(true);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    useEffect(() => {
        if (data.logs !== undefined) {
            setLogs(data.logs);
        }
    }, [data.logs]);

    useEffect(() => {
        if (!data.status) return;
        setDone(data.status === 'done');
        setRunning(data.status === 'running');
    }, [data.status]);

    const handleAnalyze = async () => {
        if (!data.nodeId || !data.onAnalyze) {
            setLogs(['⚠️ 먼저 소스 노드를 연결하세요']);
            return;
        }
        if (isMountedRef.current) {
            setRunning(true);
            setLogs(['> Gemini 분석 시작...', '> 시각적 DNA 추출 중...']);
        }
        try {
            await data.onAnalyze(data.nodeId);
            if (!isMountedRef.current) return;
            setLogs(['> 분석 완료!', '> Claude 브리프 생성됨!', '✓ 파이프라인 완료']);
            setDone(true);
        } catch (e) {
            if (!isMountedRef.current) return;
            setLogs(['❌ 파이프라인 실패', `오류: ${e}`]);
        } finally {
            if (isMountedRef.current) {
                setRunning(false);
            }
        }
    };

    return (
        <NodeWrapper title="AI 프로세서" colorClass="border-violet-500/40" status={done ? 'done' : running ? 'running' : 'idle'}>
            <Handle type="target" position={Position.Left} className={HANDLE_STYLES.violet} />
            <div className="space-y-4">
                <div className="flex justify-between items-center">
                    <span className="text-[10px] text-white/50 uppercase tracking-wider font-medium">작업</span>
                    <span className="text-[10px] font-bold text-violet-300 bg-violet-500/20 border border-violet-500/30 px-2 py-0.5 rounded shadow-[0_0_10px_rgba(139,92,246,0.2)]">AI 리믹스</span>
                </div>

                <div className="p-3 bg-black/60 rounded-lg border border-white/10 text-[10px] font-mono text-white/70 max-h-24 overflow-y-auto custom-scrollbar shadow-inner">
                    {logs.map((log, i) => <div key={i} className={log.startsWith('>') ? 'text-violet-300' : log.startsWith('✓') ? 'text-emerald-300' : 'text-white/60'}>{log}</div>)}
                </div>

                {!done && (
                    <button
                        onClick={handleAnalyze}
                        disabled={running}
                        className="w-full py-2.5 bg-gradient-to-r from-violet-600 to-violet-500 hover:from-violet-500 hover:to-violet-400 disabled:from-violet-900 disabled:to-violet-900 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(139,92,246,0.2)] hover:shadow-[0_0_25px_rgba(139,92,246,0.4)] flex items-center justify-center gap-2"
                    >
                        {running ? (
                            <>
                                <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                <span>처리 중...</span>
                            </>
                        ) : (
                            <span>🧠 파이프라인 실행</span>
                        )}
                    </button>
                )}
            </div>
            <Handle type="source" position={Position.Right} className="!bg-violet-500 !w-3 !h-3 !border-2 !border-black" />
        </NodeWrapper>
    );
});

ProcessNode.displayName = 'ProcessNode';

interface OutputNodeData {
    nodeId?: string;
    onExport?: (nodeId: string) => void;
    onPreview?: () => void;
}

export const OutputNode = memo(({ data }: { data: OutputNodeData }) => {
    const handleExport = () => {
        if (data.nodeId && data.onExport) {
            data.onExport(data.nodeId);
        } else {
            window.location.href = '/';
        }
    };

    return (
        <NodeWrapper title="최종 템플릿" colorClass="border-cyan-500/40">
            <Handle type="target" position={Position.Left} className={HANDLE_STYLES.cyan} />
            <div className="space-y-4">
                <div className="aspect-video bg-black rounded-xl border border-white/10 flex items-center justify-center relative group cursor-pointer overflow-hidden shadow-2xl">
                    <div className="absolute inset-0 bg-gradient-to-br from-cyan-900/40 via-transparent to-transparent opacity-60"></div>

                    {data.nodeId ? (
                        <div className="z-10 text-center">
                            <span className="text-4xl filter drop-shadow-[0_0_10px_rgba(6,182,212,0.8)]">🎬</span>
                            <div className="mt-2 text-[10px] text-cyan-300 font-mono bg-black/50 px-2 py-0.5 rounded">ID: {data.nodeId.slice(0, 8)}...</div>
                        </div>
                    ) : (
                        <span className="text-3xl z-10 opacity-50 group-hover:opacity-100 group-hover:scale-110 transition-all duration-300">🎬</span>
                    )}

                    <div className="absolute bottom-0 left-0 right-0 p-3 bg-black/80 backdrop-blur text-[10px] text-center text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity">
                        결과 미리보기
                    </div>
                </div>

                {/* Storyboard Preview Button */}
                <button
                    onClick={data.onPreview}
                    className="w-full py-2 bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/30 text-violet-300 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 hover:shadow-[0_0_15px_rgba(139,92,246,0.15)] group"
                >
                    <span className="group-hover:scale-110 transition-transform">🎞️</span> 스토리보드 미리보기
                </button>

                <button
                    onClick={handleExport}
                    className="w-full py-2.5 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white text-xs font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(6,182,212,0.2)] hover:shadow-[0_0_25px_rgba(6,182,212,0.4)]"
                >
                    {data.nodeId ? '🔗 템플릿 보기' : '📤 템플릿 내보내기'}
                </button>
            </div>
        </NodeWrapper>
    );
});

OutputNode.displayName = 'OutputNode';

interface NotebookNodeData {
    summary?: string;
    clusterId?: string;
    sourceUrl?: string;
}

export const NotebookNode = memo(({ data }: { data: NotebookNodeData }) => {
    const summary = data.summary || 'NotebookLM 요약을 불러오는 중입니다.';
    const clusterId = data.clusterId || 'Cluster 미지정';

    return (
        <NodeWrapper title="Notebook Library" colorClass="border-sky-500/40">
            <Handle type="target" position={Position.Left} className={HANDLE_STYLES.sky} />
            <div className="space-y-3">
                <div className="text-[10px] text-sky-300 uppercase tracking-widest">클러스터</div>
                <div className="text-xs text-white/80 font-mono bg-sky-500/10 border border-sky-500/20 px-3 py-2 rounded-lg">
                    {clusterId}
                </div>
                <div className="text-[10px] text-white/40 uppercase tracking-widest">요약</div>
                <div className="text-xs text-white/70 bg-black/50 border border-white/10 rounded-lg px-3 py-2 max-h-24 overflow-y-auto custom-scrollbar">
                    {summary}
                </div>
                {data.sourceUrl && (
                    <a
                        href={data.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-sky-300 hover:text-sky-200 underline underline-offset-2"
                        onClick={(e) => e.stopPropagation()}
                    >
                        원본 링크 열기
                    </a>
                )}
            </div>
            <Handle type="source" position={Position.Right} className={HANDLE_STYLES.sky} />
        </NodeWrapper>
    );
});

NotebookNode.displayName = 'NotebookNode';

// Tier configuration for CrawlerOutlierNode
const CRAWLER_TIER_CONFIG = {
    S: { label: 'S', icon: Award, colorClass: 'text-amber-400', bgClass: 'bg-amber-500/20', borderClass: 'border-amber-500/40' },
    A: { label: 'A', icon: Star, colorClass: 'text-purple-400', bgClass: 'bg-purple-500/20', borderClass: 'border-purple-500/40' },
    B: { label: 'B', icon: Diamond, colorClass: 'text-blue-400', bgClass: 'bg-blue-500/20', borderClass: 'border-blue-500/40' },
    C: { label: 'C', icon: BarChart, colorClass: 'text-zinc-400', bgClass: 'bg-zinc-500/20', borderClass: 'border-zinc-500/40' },
};

const CRAWLER_PLATFORM_CONFIG = {
    tiktok: { label: 'TikTok', icon: '🎵', gradient: 'from-pink-600/30 to-cyan-600/20' },
    youtube: { label: 'Shorts', icon: '▶️', gradient: 'from-red-600/30 to-gray-600/20' },
    instagram: { label: 'Reels', icon: '📷', gradient: 'from-purple-600/30 to-orange-600/20' },
};

// Note: formatViewCount is now imported from ./utils

interface CrawlerOutlierNodeData {
    outlier: CrawlerOutlierItem;
    onPromote?: (item: CrawlerOutlierItem) => void;
}

export const CrawlerOutlierNode = memo(({ data }: { data: CrawlerOutlierNodeData }) => {
    const { outlier, onPromote } = data;
    const tierConfig = outlier.outlier_tier ? CRAWLER_TIER_CONFIG[outlier.outlier_tier] : null;
    const platformConfig = CRAWLER_PLATFORM_CONFIG[outlier.platform];
    const TierIcon = tierConfig?.icon || BarChart;

    const multiplier = outlier.creator_avg_views > 0
        ? Math.round(outlier.view_count / outlier.creator_avg_views)
        : 0;

    const isPromoted = outlier.status === 'promoted';

    return (
        <NodeWrapper
            title={`${platformConfig.icon} ${tierConfig?.label || ''}-Tier Outlier`}
            colorClass={tierConfig?.borderClass || 'border-white/20'}
            status={isPromoted ? 'done' : 'idle'}
        >
            <div className="space-y-3">
                {/* Thumbnail with Platform Badge */}
                <div className={`relative aspect-video rounded-xl overflow-hidden bg-gradient-to-br ${platformConfig.gradient}`}>
                    {outlier.thumbnail_url ? (
                        <img
                            src={outlier.thumbnail_url}
                            alt={outlier.title}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-4xl opacity-50">
                            {platformConfig.icon}
                        </div>
                    )}
                    {/* Tier Badge - using shared component */}
                    <div className="absolute top-2 left-2">
                        <TierBadge tier={outlier.outlier_tier} size="sm" showIcon />
                    </div>
                    {/* Views Badge */}
                    <div className="absolute top-2 right-2">
                        <OutlierMetrics viewCount={outlier.view_count} layout="compact" />
                    </div>
                </div>

                {/* Title */}
                <div className="text-sm font-bold text-white leading-tight line-clamp-2">
                    {outlier.title || 'Untitled'}
                </div>

                {/* Stats Row */}
                <div className="flex items-center gap-3 text-xs text-white/60">
                    {multiplier > 0 && (
                        <span className={`flex items-center gap-1 font-mono font-bold ${tierConfig?.colorClass || 'text-white/60'}`}>
                            <Zap className="w-3 h-3" />
                            {multiplier}x
                        </span>
                    )}
                    {typeof outlier.engagement_rate === 'number' && (
                        <>
                            <span className="text-white/40">•</span>
                            <span>{(outlier.engagement_rate * 100).toFixed(1)}% Eng</span>
                        </>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2 border-t border-white/10">
                    <a
                        href={outlier.video_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-[10px] text-white/70 hover:text-white transition-all"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <ExternalLink className="w-3 h-3" />
                        View
                    </a>
                    {!isPromoted && onPromote && (
                        <button
                            onClick={() => onPromote(outlier)}
                            className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg font-bold text-[10px] transition-all ${tierConfig?.bgClass || 'bg-violet-500/20'} ${tierConfig?.borderClass || 'border-violet-500/40'} border ${tierConfig?.colorClass || 'text-violet-300'} hover:brightness-125`}
                        >
                            <Star className="w-3 h-3" />
                            Promote
                        </button>
                    )}
                    {isPromoted && (
                        <div className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-[10px] text-emerald-400 font-bold">
                            ✓ Promoted
                        </div>
                    )}
                </div>
            </div>
            <Handle type="source" position={Position.Right} className="!bg-violet-500 !w-3 !h-3 !border-2 !border-black" />
        </NodeWrapper>
    );
});

CrawlerOutlierNode.displayName = 'CrawlerOutlierNode';

/**
 * Template Seed Node - Opal-generated template seeds
 * Based on 15_FINAL_ARCHITECTURE.md
 */
interface TemplateSeedData {
    seed_id: string;
    template_type: 'capsule' | 'guide' | 'edit';
    hook?: string;
    shotlist?: string[];
    audio?: string;
    timing?: string[];
    parent_id?: string;
    cluster_id?: string;
}

interface TemplateSeedNodeData {
    seed: TemplateSeedData;
    onApply?: (seed: TemplateSeedData) => void;
}

const TEMPLATE_TYPE_CONFIG = {
    capsule: { label: 'Capsule', icon: '💊', colorClass: 'text-emerald-400', bgClass: 'bg-emerald-500/20' },
    guide: { label: 'Guide', icon: '📋', colorClass: 'text-blue-400', bgClass: 'bg-blue-500/20' },
    edit: { label: 'Edit', icon: '✂️', colorClass: 'text-orange-400', bgClass: 'bg-orange-500/20' },
};

export const TemplateSeedNode = memo(({ data }: { data: TemplateSeedNodeData }) => {
    const { seed, onApply } = data;
    const typeConfig = TEMPLATE_TYPE_CONFIG[seed.template_type] || TEMPLATE_TYPE_CONFIG.capsule;

    return (
        <NodeWrapper
            title={`${typeConfig.icon} Template Seed`}
            colorClass="border-emerald-500/40"
            status="idle"
        >
            <div className="space-y-3">
                {/* Type Badge */}
                <div className="flex items-center justify-between">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${typeConfig.bgClass} ${typeConfig.colorClass}`}>
                        {typeConfig.label}
                    </span>
                    <span className="text-[9px] text-white/30 font-mono">{seed.seed_id?.slice(0, 12)}...</span>
                </div>

                {/* Hook */}
                {seed.hook && (
                    <div>
                        <div className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Hook</div>
                        <div className="text-sm text-white/90 leading-snug">{seed.hook}</div>
                    </div>
                )}

                {/* Shotlist Preview */}
                {seed.shotlist && seed.shotlist.length > 0 && (
                    <div>
                        <div className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Shots ({seed.shotlist.length})</div>
                        <div className="space-y-1">
                            {seed.shotlist.slice(0, 3).map((shot, i) => (
                                <div key={i} className="text-[11px] text-white/60 truncate flex items-center gap-1">
                                    <span className="w-4 h-4 rounded-full bg-white/10 flex items-center justify-center text-[9px]">{i + 1}</span>
                                    {typeof shot === 'string' ? shot : (shot as { description?: string })?.description || ''}
                                </div>
                            ))}
                            {seed.shotlist.length > 3 && (
                                <div className="text-[10px] text-white/40">+{seed.shotlist.length - 3} more...</div>
                            )}
                        </div>
                    </div>
                )}

                {/* Timing */}
                {seed.timing && seed.timing.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                        {seed.timing.slice(0, 5).map((t, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-white/5 rounded text-[9px] text-white/50 font-mono">{t}</span>
                        ))}
                    </div>
                )}

                {/* Apply Button */}
                {onApply && (
                    <button
                        onClick={() => onApply(seed)}
                        className="w-full py-2 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 text-xs font-bold hover:bg-emerald-500/30 hover:border-emerald-500/60 hover:shadow-[0_0_15px_rgba(16,185,129,0.2)] transition-all"
                    >
                        ✨ Apply Seed
                    </button>
                )}
            </div>
            <Handle type="target" position={Position.Left} className={HANDLE_STYLES.emerald} />
            <Handle type="source" position={Position.Right} className={HANDLE_STYLES.emerald} />
        </NodeWrapper>
    );
});

TemplateSeedNode.displayName = 'TemplateSeedNode';

export interface GuideNodeData {
    hook: string;
    shotlist: string[];
    audio: string;
    scene: string;
    timing: string[];
    do_not?: string[];
    nodeId?: string;  // For navigation context
}

export const GuideNode = memo(({ data }: { data: GuideNodeData }) => {
    const router = useRouter();
    return (
        <NodeWrapper
            title="Guide: Short-Form"
            colorClass="border-cyan-500/40"
            status="done"
        >
            <div className="space-y-4">
                {/* Hook Section */}
                <div>
                    <div className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider mb-1">Hook (0-2s)</div>
                    <div className="p-4 bg-gradient-to-br from-cyan-950/30 to-black/20 border border-cyan-500/20 rounded-xl text-sm text-cyan-50 font-bold leading-relaxed shadow-inner">
                        "{data.hook}"
                    </div>
                </div>

                {/* Shotlist */}
                <div>
                    <div className="text-[10px] text-white/40 uppercase tracking-wider mb-2">Sequence</div>
                    <div className="space-y-1">
                        {data.shotlist.map((shot, i) => (
                            <div key={i} className="flex gap-3 items-start p-2 bg-black/20 rounded-lg hover:bg-white/5 transition-colors">
                                <span className="text-[10px] text-cyan-500 font-mono mt-0.5">{(i + 1).toString().padStart(2, '0')}</span>
                                <div className="space-y-1">
                                    <div className="text-xs text-white/90 leading-snug">{typeof shot === 'string' ? shot : (shot as { description?: string })?.description || ''}</div>
                                    {data.timing?.[i] && (
                                        <span className="inline-block px-1.5 py-0.5 rounded bg-white/10 text-[9px] text-white/40 font-mono">
                                            {data.timing[i]}s
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Audio & Mood */}
                <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 border border-white/10 rounded-lg bg-white/5">
                        <div className="text-[9px] text-white/40 uppercase mb-1">Audio</div>
                        <div className="text-xs text-cyan-300 truncate">🎵 {data.audio}</div>
                    </div>
                    <div className="p-2 border border-white/10 rounded-lg bg-white/5">
                        <div className="text-[9px] text-white/40 uppercase mb-1">Scene</div>
                        <div className="text-xs text-purple-300 truncate">🎬 {data.scene}</div>
                    </div>
                </div>

                {/* Do Not */}
                {data.do_not && data.do_not.length > 0 && (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                        <div className="text-[9px] text-red-400 font-bold uppercase mb-1">Warning (Do Not)</div>
                        <ul className="list-disc list-inside text-xs text-red-300/80 space-y-1">
                            {data.do_not.map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Next Step CTA */}
                <div className="pt-3 border-t border-white/10 space-y-2">
                    <button
                        onClick={() => router.push('/wizard')}
                        className="w-full py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-white text-sm font-bold rounded-xl transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)]"
                    >
                        <Camera className="w-4 h-4" />
                        🎬 Shoot 시작하기
                    </button>
                    {data.nodeId && (
                        <button
                            onClick={() => router.push(`/remix/${data.nodeId}`)}
                            className="w-full py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 text-xs font-medium rounded-lg transition-all flex items-center justify-center gap-2"
                        >
                            <ExternalLink className="w-3 h-3" />
                            상세 편집 페이지
                        </button>
                    )}
                </div>
            </div>
            <Handle type="target" position={Position.Left} className={HANDLE_STYLES.cyan} />
            <Handle type="source" position={Position.Right} className={HANDLE_STYLES.cyan} />
        </NodeWrapper>
    );
});

GuideNode.displayName = 'GuideNode';
