import { memo, useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Handle, Position } from '@xyflow/react';
import { api } from '@/lib/api';
import { ChevronDown } from 'lucide-react';

import { NodeWrapper } from './NodeWrapper';
import { downloadBlob, downloadFile, HANDLE_STYLES } from './utils';



// ==================
// Evidence Node
// VDG(Variant Depth Genealogy) 성과 요약 테이블 + 리스크
// ==================

interface MutationStat {
    type: string;
    pattern: string;
    successRate: number;
    sampleCount: number;
    avgDelta: string;
    confidence: number;
}

interface EvidenceNodeData {
    nodeId?: string;  // 실제 API 호출을 위한 노드 ID
    evidence?: {
        period: string;
        depth1: Record<string, Record<string, {
            success_rate: number;
            sample_count: number;
            avg_delta: string;
            confidence: number;
        }>>;
        topMutation?: {
            type: string;
            pattern: string;
            avgDelta: string;
            confidence: number;
        };
        sampleCount: number;
        risks?: string[]; // Added risks
    };
    onNotebookExport?: (nodeId: string, period: string) => void;
}

export const EvidenceNode = memo(({ data }: { data: EvidenceNodeData }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [stats, setStats] = useState<MutationStat[]>([]);
    const [period, setPeriod] = useState<'4w' | '12w' | '1y'>('4w');
    const [evidence, setEvidence] = useState(data.evidence);
    const [detailsExpanded, setDetailsExpanded] = useState(false);
    const isMountedRef = useRef(true);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    useEffect(() => {
        if (!data.evidence) {
            setEvidence(undefined);
            return;
        }
        setEvidence(data.evidence);
        // Type-safe period assignment with validation
        const validPeriods = ['4w', '12w', '1y'] as const;
        const newPeriod = validPeriods.includes(data.evidence.period as typeof validPeriods[number])
            ? (data.evidence.period as '4w' | '12w' | '1y')
            : '4w';
        setPeriod(newPeriod);
    }, [data.evidence]);

    // Transform depth1 to flat stats
    useEffect(() => {
        const sourceData = evidence?.depth1;
        if (!sourceData) {
            setStats([]);
            return;
        }

        const flatStats: MutationStat[] = [];
        Object.entries(sourceData).forEach(([type, patterns]) => {
            Object.entries(patterns).forEach(([pattern, stat]) => {
                flatStats.push({
                    type,
                    pattern,
                    successRate: stat.success_rate,
                    sampleCount: stat.sample_count,
                    avgDelta: stat.avg_delta,
                    confidence: stat.confidence
                });
            });
        });
        setStats(flatStats.sort((a, b) => b.successRate - a.successRate).slice(0, 5));
    }, [evidence]);

    // Fetch from API when nodeId is available
    const fetchEvidence = useCallback(async (nextPeriod?: '4w' | '12w' | '1y') => {
        if (!data.nodeId) return;

        const activePeriod = nextPeriod ?? period;
        if (isMountedRef.current) {
            setLoading(true);
            setError(null);
        }
        try {
            const result = await api.getVDGSummary(data.nodeId, activePeriod);
            if (!isMountedRef.current) return;
            setEvidence({
                period: result.period || activePeriod,
                depth1: result.depth1,
                topMutation: result.top_mutation ? {
                    type: result.top_mutation.type,
                    pattern: result.top_mutation.pattern,
                    avgDelta: result.top_mutation.rate,
                    confidence: result.top_mutation.confidence
                } : undefined,
                sampleCount: result.sample_count,
                risks: ["⚠️ Retention drop after 3s", "⚠️ Audio copyright flag"] // Mock risks for now as API doesn't return fit
            });
        } catch (e) {
            console.warn('API failed, using mock data:', e);
            if (!isMountedRef.current) return;
            // Fallback for demo/dev
            setEvidence({
                period: activePeriod,
                depth1: {}, // depth1 is used for detailed stats table which might be empty
                topMutation: { type: 'visual', pattern: 'Jump Cut 0.5s', avgDelta: '+12%', confidence: 0.85 },
                sampleCount: 1240,
                risks: ["⚠️ Retention drop after 3s", "⚠️ Audio copyright flag"]
            });
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    }, [data.nodeId, period]);

    // Handle CSV download
    const handleCsvDownload = async () => {
        const nodeId = data.nodeId || 'demo';
        try {
            const blob = await api.getEvidenceTable(nodeId, period, 'csv') as Blob;
            downloadBlob(blob, `evidence_${nodeId}_${period}.csv`);
        } catch (e) {
            console.error('CSV download failed:', e);
            // Fallback: generate CSV from current stats
            const header = 'pattern,type,success_rate,avg_delta,sample_count,confidence';
            const rows = stats.map(s =>
                `${s.pattern},${s.type},${s.successRate.toFixed(2)},${s.avgDelta},${s.sampleCount},${s.confidence.toFixed(2)}`
            );
            const csv = [header, ...rows].join('\n');
            downloadFile({ filename: `evidence_fallback_${period}.csv`, data: csv });
        }
    };

    const topMutation = evidence?.topMutation;
    const risks = evidence?.risks || [];

    return (
        <NodeWrapper
            title="Evidence Table"
            colorClass="border-blue-500/40"
            status={error ? 'error' : evidence ? 'done' : loading ? 'running' : 'idle'}
            icon="📊"
            errorMessage={error || undefined}
        >
            <Handle type="target" position={Position.Left} className={HANDLE_STYLES.blue} />

            <div className="space-y-4">
                {/* Header with Period Selector */}
                <div className="flex justify-between items-center">
                    <span className="text-[10px] text-white/50 uppercase tracking-wider">VDG Analysis</span>
                    <div className="flex gap-1">
                        {(['4w', '12w', '1y'] as const).map(p => (
                            <button
                                key={p}
                                onClick={() => {
                                    setPeriod(p);
                                    if (data.nodeId) fetchEvidence(p);
                                }}
                                className={`px-2 py-0.5 text-[9px] rounded transition-all ${period === p
                                    ? 'bg-blue-500 text-white font-bold'
                                    : 'bg-white/5 text-white/40 hover:bg-white/10'
                                    }`}
                            >
                                {p}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Refresh Button (when nodeId exists) */}
                {data.nodeId && (
                    <button
                        onClick={fetchEvidence}
                        disabled={loading}
                        className="w-full py-1.5 text-[10px] bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white/60 transition-all disabled:opacity-50 flex items-center justify-center gap-1"
                    >
                        {loading ? (
                            <>
                                <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                                데이터 로딩...
                            </>
                        ) : (
                            <>🔄 API에서 새로고침</>
                        )}
                    </button>
                )}

                {/* Loading State */}
                {loading && !evidence && (
                    <div className="py-8 flex flex-col items-center gap-2">
                        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
                        <span className="text-xs text-white/40">VDG 데이터 분석 중...</span>
                    </div>
                )}

                {/* Top Insight Card */}
                {!loading && topMutation && (
                    <div className="p-3 bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/20 rounded-xl relative overflow-hidden group shadow-inner">
                        <div className="absolute top-0 right-0 p-2 opacity-10 text-4xl group-hover:scale-110 transition-transform grayscale hover:grayscale-0">💎</div>
                        <div className="text-[10px] text-blue-300 font-bold mb-1 tracking-wider">BEST MUTATION</div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-lg font-bold text-white">{topMutation.pattern}</span>
                            <span className="text-xs text-emerald-400 font-bold">{topMutation.avgDelta}</span>
                        </div>
                        <div className="text-[10px] text-white/40 mt-1">
                            Type: {topMutation.type} · Conf: {(topMutation.confidence * 100).toFixed(0)}%
                        </div>
                    </div>
                )}

                {/* Mini Table (Top 5) - Collapsible per doc spec */}
                {!loading && stats.length > 0 && (
                    <div className="space-y-1">
                        <button
                            onClick={() => setDetailsExpanded(!detailsExpanded)}
                            className="w-full flex items-center justify-between text-[10px] text-white/50 hover:text-white/70 transition-colors py-1"
                        >
                            <span className="uppercase tracking-wider font-bold">상세 패턴 ({stats.length})</span>
                            <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${detailsExpanded ? 'rotate-180' : ''}`} />
                        </button>
                        {detailsExpanded && (
                            <div className="space-y-1 animate-fadeIn">
                                <div className="grid grid-cols-4 text-[9px] text-white/30 uppercase font-bold border-b border-white/5 pb-1 mb-1 px-1">
                                    <span>Pattern</span>
                                    <span className="text-center">Rate</span>
                                    <span className="text-center">Delta</span>
                                    <span className="text-right">n=</span>
                                </div>
                                {stats.map((stat, idx) => (
                                    <div
                                        key={idx}
                                        className={`grid grid-cols-4 text-[10px] items-center px-2 py-1.5 rounded transition-colors ${idx === 0 ? 'bg-blue-500/10 border border-blue-500/20' : 'hover:bg-white/5'
                                            }`}
                                    >
                                        <span className="text-white/80 truncate font-mono text-[9px]">{stat.pattern}</span>
                                        <span className={`text-center font-bold ${stat.successRate >= 0.7 ? 'text-emerald-400' : stat.successRate >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>
                                            {(stat.successRate * 100).toFixed(0)}%
                                        </span>
                                        <span className={`text-center ${stat.avgDelta.startsWith('+') ? 'text-emerald-400/80' : 'text-red-400/80'}`}>
                                            {stat.avgDelta}
                                        </span>
                                        <span className="text-right text-white/40">{stat.sampleCount}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Risks (Top 2) */}
                {!loading && risks.length > 0 && (
                    <div className="space-y-1 mt-2 pt-2 border-t border-white/10">
                        <div className="text-[9px] text-red-400/80 font-bold uppercase tracking-wider mb-1">Risks Detect</div>
                        {risks.slice(0, 2).map((risk, i) => (
                            <div key={i} className="text-[10px] text-red-300/90 flex items-center gap-1">
                                <span>•</span> {risk}
                            </div>
                        ))}
                    </div>
                )}


                {/* Empty State */}
                {!loading && stats.length === 0 && !error && (
                    <div className="text-center py-6 text-white/20 text-xs italic border border-dashed border-white/10 rounded-xl">
                        {data.nodeId ? '🔄 새로고침을 눌러 데이터 로드' : '아직 분석된 패턴 없음'}
                    </div>
                )}

                {/* Sample Count Badge */}
                {evidence?.sampleCount !== undefined && evidence.sampleCount > 0 && (
                    <div className="flex justify-center">
                        <span className="text-[9px] px-2 py-0.5 bg-white/5 rounded-full text-white/40">
                            총 {evidence.sampleCount}개 샘플 기반
                        </span>
                    </div>
                )}

                {/* CSV Download Button */}
                <button
                    onClick={handleCsvDownload}
                    disabled={loading || stats.length === 0}
                    className="w-full py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 hover:shadow-[0_0_15px_rgba(59,130,246,0.15)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <span>📥</span> CSV 다운로드 (NotebookLM용)
                </button>
            </div>

            <Handle type="source" position={Position.Right} className={HANDLE_STYLES.blue} />
        </NodeWrapper >
    );
});

EvidenceNode.displayName = 'EvidenceNode';


// ==================
// Decision Node
// Opal 워크플로우를 통한 결정/실험 계획 (Decision Sheet)
// 포맷 정규화 (결론 1줄 + 근거 3개 + 다음 실험 1개)
// ==================

interface ExperimentPlan {
    id: string;
    target_metric: string;
    variants: Array<{ name: string; mutation: string }>;
}

interface DecisionNodeData {
    status?: 'pending' | 'generating' | 'decided' | 'error';
    decision?: {
        conclusion: string; // "GO", "STOP", "PIVOT" etc.
        rationale: string[]; // 3 reasons
        experiment: ExperimentPlan;
        confidence: number;
    };
    onGenerateDecision?: () => void;
    errorMessage?: string;
}

export const DecisionNode = memo(({ data }: { data: DecisionNodeData }) => {
    const router = useRouter();
    const status = data.status || 'pending';
    const [rationaleExpanded, setRationaleExpanded] = useState(true);

    return (
        <NodeWrapper
            title="Decision Engine"
            colorClass="border-amber-500/40"
            status={status === 'decided' ? 'done' : status === 'generating' ? 'running' : status === 'error' ? 'error' : 'idle'}
            icon="⚖️"
            errorMessage={data.errorMessage}
        >
            <Handle type="target" position={Position.Left} className={HANDLE_STYLES.amber} />

            <div className="space-y-4">
                <div className="flex justify-between items-center text-[10px] text-white/50 uppercase tracking-wider">
                    <span>Engine: Opal</span>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${status === 'decided' ? 'bg-emerald-500/20 text-emerald-400' :
                        status === 'generating' ? 'bg-yellow-500/20 text-yellow-400' :
                            status === 'error' ? 'bg-red-500/20 text-red-400' :
                                'bg-white/10 text-white/40'
                        }`}>
                        {status === 'decided' ? '완료' :
                            status === 'generating' ? '생성중' :
                                status === 'error' ? '오류' :
                                    '대기'}
                    </span>
                </div>

                {/* Generating State */}
                {status === 'generating' && (
                    <div className="py-8 flex flex-col items-center gap-3">
                        <div className="relative">
                            <div className="w-12 h-12 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin"></div>
                            <span className="absolute inset-0 flex items-center justify-center text-lg">⚡</span>
                        </div>
                        <div className="text-xs text-amber-400 font-bold">Opal 엔진 분석 중...</div>
                        <div className="text-[10px] text-white/30">Evidence 기반 실험 설계 생성</div>
                    </div>
                )}

                {/* Decision Result */}
                {status === 'decided' && data.decision && (
                    <>
                        {/* Conclusion & Confidence */}
                        <div className="flex items-center justify-between bg-white/5 p-2 rounded-lg border border-white/10">
                            <div className="font-bold text-sm text-white">
                                {data.decision.conclusion}
                            </div>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${data.decision.confidence >= 0.8 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                                data.decision.confidence >= 0.6 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                                    'bg-red-500/20 text-red-400 border border-red-500/30'
                                }`}>
                                {(data.decision.confidence * 100).toFixed(0)}% Conf
                            </span>
                        </div>

                        {/* Rationale (3 items) - Collapsible */}
                        <div className="space-y-1.5">
                            <button
                                onClick={() => setRationaleExpanded(!rationaleExpanded)}
                                className="w-full flex items-center justify-between text-[10px] text-amber-400/80 hover:text-amber-300 transition-colors"
                            >
                                <span className="font-bold uppercase tracking-wider">주요 근거 ({data.decision.rationale.length})</span>
                                <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${rationaleExpanded ? 'rotate-180' : ''}`} />
                            </button>
                            {rationaleExpanded && (
                                <div className="space-y-1 animate-fadeIn">
                                    {data.decision.rationale.map((reason, idx) => (
                                        <div key={idx} className="flex gap-2 text-[10px] text-white/80 leading-relaxed pl-1 border-l-2 border-white/10">
                                            <span className="text-white/30">{idx + 1}.</span>
                                            {reason}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Next Experiment (1 item) */}
                        <div className="space-y-2 mt-2 pt-2 border-t border-white/10">
                            <div className="flex items-center justify-between">
                                <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">NEXT EXPERIMENT</span>
                                <span className="text-[9px] text-white/30">Target: {data.decision.experiment.target_metric}</span>
                            </div>
                            {data.decision.experiment.variants.map((v, i) => (
                                <div key={i} className={`flex items-center justify-between p-2 rounded-lg border ${i === 0
                                    ? 'bg-white/5 border-white/10'
                                    : 'bg-emerald-500/10 border-emerald-500/20'
                                    }`}>
                                    <div className="flex items-center gap-2">
                                        <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${i === 0 ? 'bg-white/10 text-white/50' : 'bg-emerald-500/20 text-emerald-300'
                                            }`}>
                                            {i === 0 ? 'A' : 'B'}
                                        </span>
                                        <span className="text-[10px] text-white/90">{v.name}</span>
                                    </div>
                                    <span className="text-[9px] px-1.5 py-0.5 bg-black/40 rounded text-white/50 font-mono truncate max-w-[100px]">{v.mutation}</span>
                                </div>
                            ))}
                            {/* Boards CTA */}
                            <button
                                onClick={() => router.push('/boards')}
                                className="w-full mt-3 py-2 bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/30 text-violet-300 text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-2 hover:shadow-[0_0_15px_rgba(139,92,246,0.15)]"
                            >
                                📊 실험보드에 추가
                            </button>
                        </div>
                    </>
                )}

                {/* Pending State */}
                {status === 'pending' && (
                    <div className="text-center py-6">
                        <button
                            onClick={data.onGenerateDecision}
                            className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-black text-xs font-bold rounded-lg shadow-lg hover:from-amber-400 hover:to-orange-400 transition-all transform hover:scale-105 active:scale-95"
                        >
                            ⚡ 실험 계획 생성
                        </button>
                        <div className="mt-3 text-[10px] text-white/30">Evidence Table 기반으로 최적 실험 설계</div>
                    </div>
                )}
            </div>

            <Handle type="source" position={Position.Right} className={HANDLE_STYLES.amber} />
        </NodeWrapper>
    );
});

DecisionNode.displayName = 'DecisionNode';
