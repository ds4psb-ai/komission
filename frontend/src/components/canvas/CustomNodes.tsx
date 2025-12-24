import { memo, useState } from 'react';
import { Handle, Position } from '@xyflow/react';
import { RemixNode } from '@/lib/api';

interface NodeWrapperProps {
    children: React.ReactNode;
    title: string;
    colorClass: string;
    status?: 'idle' | 'running' | 'done' | 'error';
    isLocked?: boolean;  // Governance: Brand protection (Master node)
    isVariableSlot?: boolean;  // Phase 4: Editable/customizable slot
    viralBadge?: string; // Viral performance insight
}

const NodeWrapper = ({ children, title, colorClass, status, isLocked, isVariableSlot, viralBadge }: NodeWrapperProps) => {
    // Governance styling: locked = gold border + glow (Master nodes)
    const lockedStyles = isLocked
        ? 'border-amber-400 shadow-[0_0_30px_rgba(251,191,36,0.2)]'
        : isVariableSlot
            ? 'border-pink-500 shadow-[0_0_25px_rgba(236,72,153,0.3)] ring-2 ring-pink-500/20'
            : 'hover:shadow-[0_0_20px_rgba(255,255,255,0.15)] hover:border-white/40';

    const pulsingClass = !isLocked && status !== 'done'
        ? 'animate-[pulse_4s_ease-in-out_infinite]'
        : '';

    // Gradient header based on color class
    const headerGradient = colorClass.includes('emerald') ? 'from-emerald-900/40 to-emerald-800/20' :
        colorClass.includes('violet') ? 'from-violet-900/40 to-violet-800/20' :
            colorClass.includes('pink') && isVariableSlot ? 'from-pink-900/40 to-pink-800/20' :
                'from-cyan-900/40 to-cyan-800/20';

    return (
        <div className={`glass-panel rounded-2xl min-w-[300px] overflow-hidden border ${colorClass} ${lockedStyles} ${pulsingClass} transition-all duration-300 group`}>
            {/* Header */}
            <div className={`px-5 py-3 border-b bg-gradient-to-r ${headerGradient} flex items-center justify-between ${colorClass}`}>
                <div className="flex items-center gap-2">
                    {isLocked && <span className="text-amber-400 text-lg drop-shadow-[0_0_5px_rgba(251,191,36,0.5)]">🔒</span>}
                    {isVariableSlot && !isLocked && <span className="text-pink-400 text-lg drop-shadow-[0_0_5px_rgba(236,72,153,0.5)]">🎯</span>}
                    <span className="font-bold text-sm tracking-widest text-white/90 uppercase">{title}</span>
                    {isVariableSlot && !isLocked && (
                        <span className="text-[9px] px-2 py-0.5 bg-pink-500/20 text-pink-300 border border-pink-500/30 rounded-full font-bold">
                            편집 가능
                        </span>
                    )}
                </div>
                <div className="flex gap-2 items-center">
                    {viralBadge && (
                        <span className="text-[10px] px-2 py-0.5 bg-pink-500/20 text-pink-300 border border-pink-500/30 rounded-full font-bold shadow-[0_0_10px_rgba(236,72,153,0.3)]">
                            {viralBadge}
                        </span>
                    )}
                    <div className="flex gap-1">
                        {status === 'running' && (
                            <div className="relative w-2 h-2">
                                <div className="absolute inset-0 bg-yellow-400 rounded-full animate-ping opacity-75"></div>
                                <div className="relative w-2 h-2 bg-yellow-500 rounded-full"></div>
                            </div>
                        )}
                        {status === 'done' && <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_5px_#10b981]"></div>}
                        {status === 'error' && <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_5px_#ef4444]"></div>}
                        {!status && (
                            <>
                                <div className="w-1.5 h-1.5 rounded-full bg-white/20"></div>
                                <div className="w-1.5 h-1.5 rounded-full bg-white/20"></div>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Body */}
            <div className="p-5 bg-black/40 backdrop-blur-2xl relative">
                {/* Subtle Grid Background */}
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.03] pointer-events-none" />

                {isLocked && (
                    <div className="mb-4 px-3 py-2 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs text-amber-300 font-bold text-center shadow-[inset_0_0_10px_rgba(251,191,36,0.1)]">
                        ⚠️ 브랜드 보호 노드 - 수정 불가
                    </div>
                )}
                {isVariableSlot && !isLocked && (
                    <div className="mb-4 px-3 py-2 bg-pink-500/10 border border-pink-500/30 rounded-lg text-xs text-pink-300 font-bold text-center shadow-[inset_0_0_10px_rgba(236,72,153,0.1)]">
                        🎯 이 슬롯을 자유롭게 수정하세요!
                    </div>
                )}
                <div className="relative z-10">
                    {children}
                </div>
            </div>
        </div>
    );
};

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

    // If it's an outlier node, it's already verified
    if (data.outlier) {
        return (
            <NodeWrapper
                title={data.isLocked ? "🔒 브랜드 소스" : "소스: 아웃라이어"}
                colorClass={data.isLocked ? "border-amber-500/40" : "border-emerald-500/40"}
                status="done"
                isLocked={data.isLocked}
                viralBadge={data.viralBadge || `Layer ${data.outlier.genealogy_depth + 1}`}
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
                <Handle type="source" position={Position.Right} className="!bg-emerald-500 !w-3 !h-3 !border-2 !border-black" />
            </NodeWrapper>
        );
    }

    const handleSubmit = async () => {
        if (!url || !data.onSubmit) return;
        setLoading(true);
        try {
            await data.onSubmit(url, title || 'New Source');
            setVerified(true);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
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

    const handleAnalyze = async () => {
        if (!data.nodeId || !data.onAnalyze) {
            setLogs(['⚠️ 먼저 소스 노드를 연결하세요']);
            return;
        }
        setRunning(true);
        setLogs(['> Gemini 분석 시작...', '> 시각적 DNA 추출 중...']);
        try {
            await data.onAnalyze(data.nodeId);
            setLogs(['> 분석 완료!', '> Claude 브리프 생성됨!', '✓ 파이프라인 완료']);
            setDone(true);
        } catch (e) {
            setLogs(['❌ 파이프라인 실패', `오류: ${e}`]);
        } finally {
            setRunning(false);
        }
    };

    return (
        <NodeWrapper title="AI 프로세서" colorClass="border-violet-500/40" status={done ? 'done' : running ? 'running' : 'idle'}>
            <Handle type="target" position={Position.Left} className="!bg-violet-500 !w-3 !h-3 !border-2 !border-black" />
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
            <Handle type="target" position={Position.Left} className="!bg-cyan-500 !w-3 !h-3 !border-2 !border-black" />
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
            <Handle type="target" position={Position.Left} className="!bg-sky-500 !w-3 !h-3 !border-2 !border-black" />
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
            <Handle type="source" position={Position.Right} className="!bg-sky-500 !w-3 !h-3 !border-2 !border-black" />
        </NodeWrapper>
    );
});
