'use client';

/**
 * PatternGuidePanel - P0/P2 E2E Integration
 * 
 * 패턴 라이브러리에서 "캔버스에서 적용" 클릭 시
 * Canvas에 표시되는 가이드 패널
 * 
 * P0: invariant_rules 체크리스트 + mutation_strategy
 * P2: 촬영 완료 후 영상 제출 폼 (Feedback Loop)
 */

import { useState, useEffect } from 'react';
import { api, PatternLibraryItem } from '@/lib/api';
import { Lightbulb, Repeat, CheckCircle2, AlertTriangle, X, ChevronDown, ChevronUp, BookOpen, Download, Upload, Send, Loader2 } from 'lucide-react';
import { ViralGuideCard } from '@/components/ViralGuideCard';

interface PatternGuidePanelProps {
    patternId: string | null;
    onClose: () => void;
}

export function PatternGuidePanel({ patternId, onClose }: PatternGuidePanelProps) {
    const [pattern, setPattern] = useState<PatternLibraryItem | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [checkedRules, setCheckedRules] = useState<Set<string>>(new Set());
    const [collapsed, setCollapsed] = useState(false);
    const [showGuideCard, setShowGuideCard] = useState(false);

    // P2: Submission form state
    const [showSubmitForm, setShowSubmitForm] = useState(false);
    const [videoUrl, setVideoUrl] = useState('');
    const [creatorNotes, setCreatorNotes] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [submitMessage, setSubmitMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    // Phase 6: O2O campaigns and performance stats
    const [relatedCampaigns, setRelatedCampaigns] = useState<any[]>([]);
    const [performanceStats, setPerformanceStats] = useState<{
        avgViews: number;
        successRate: string;
        totalSubmissions: number;
    } | null>(null);

    useEffect(() => {
        setCheckedRules(new Set());
        setShowGuideCard(false);
        setShowSubmitForm(false);
        setVideoUrl('');
        setCreatorNotes('');
        setSubmitMessage(null);
        setSubmitting(false);
    }, [patternId]);

    useEffect(() => {
        let cancelled = false;
        if (!patternId) {
            setPattern(null);
            return;
        }

        const loadPattern = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await api.getPatternDetail(patternId);
                if (cancelled) return;
                setPattern(data);
            } catch (e: any) {
                if (cancelled) return;
                setError(e.message || '패턴을 불러올 수 없습니다');
                // Fallback mock for demo
                setPattern({
                    id: 'mock',
                    pattern_id: patternId,
                    cluster_id: 'demo',
                    temporal_phase: 'T1',
                    platform: 'tiktok',
                    category: 'beauty',
                    invariant_rules: {
                        "첫 2초 시선 고정": "얼굴/제품 클로즈업으로 시작",
                        "음악 싱크": "비트 드롭에 핵심 장면 배치",
                        "텍스트 오버레이": "상단 1/3에 후킹 텍스트",
                    },
                    mutation_strategy: {
                        "배경 변경": { risk: "low", impact: "+5~15%" },
                        "컬러 그레이딩": { risk: "medium", impact: "+10~25%" },
                        "트랜지션 스타일": { risk: "low", impact: "+3~8%" },
                    },
                    citations: null,
                    revision: 1,
                    created_at: new Date().toISOString(),
                });
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        };

        loadPattern();
        return () => {
            cancelled = true;
        };
    }, [patternId]);

    // Phase 6: Load related O2O campaigns and performance stats
    useEffect(() => {
        let cancelled = false;
        if (!pattern) return;

        setRelatedCampaigns([]);
        setPerformanceStats(null);

        const loadCampaignsAndStats = async () => {
            try {
                // Fetch O2O campaigns matching pattern category
                const campaigns = await api.listO2OCampaigns();
                const filtered = campaigns.filter((c: any) =>
                    c.status === 'recruiting' &&
                    (!c.category || c.category === pattern.category)
                );
                if (cancelled) return;
                setRelatedCampaigns(filtered.slice(0, 3));

                // Extract performance from mutation_strategy._creator_feedback
                const feedback = pattern.mutation_strategy?._creator_feedback;
                if (Array.isArray(feedback) && feedback.length > 0) {
                    const totalViews = feedback.reduce((sum: number, f: any) => sum + (f.views || 0), 0);
                    const avgViews = Math.round(totalViews / feedback.length);
                    const successCount = feedback.filter((f: any) =>
                        f.performance && f.performance.startsWith('+')
                    ).length;
                    const successRate = `${Math.round((successCount / feedback.length) * 100)}%`;

                    if (cancelled) return;
                    setPerformanceStats({
                        avgViews,
                        successRate,
                        totalSubmissions: feedback.length,
                    });
                }
            } catch (e) {
                console.error('Failed to load campaigns/stats:', e);
            }
        };

        loadCampaignsAndStats();
        return () => {
            cancelled = true;
        };
    }, [pattern]);

    if (!patternId) return null;

    const toggleRule = (rule: string) => {
        setCheckedRules(prev => {
            const next = new Set(prev);
            if (next.has(rule)) {
                next.delete(rule);
            } else {
                next.add(rule);
            }
            return next;
        });
    };

    const invariantRules = pattern?.invariant_rules || {};
    const mutationStrategy = pattern?.mutation_strategy || {};
    const completedCount = checkedRules.size;
    const totalCount = Object.keys(invariantRules).length;
    const completionPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

    const getRiskColor = (risk: string) => {
        switch (risk) {
            case 'low': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
            case 'medium': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
            case 'high': return 'text-red-400 bg-red-500/10 border-red-500/30';
            default: return 'text-white/60 bg-white/5 border-white/20';
        }
    };

    const getRiskLabel = (risk: string) => {
        switch (risk) {
            case 'low': return '안전';
            case 'medium': return '주의';
            case 'high': return '위험';
            default: return risk;
        }
    };

    return (
        <div className="bg-gradient-to-b from-violet-900/20 to-black/40 border border-violet-500/30 rounded-xl overflow-hidden backdrop-blur-xl shadow-2xl shadow-violet-500/10">
            {/* Header */}
            <div
                className="px-4 py-3 border-b border-violet-500/20 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
                onClick={() => setCollapsed(!collapsed)}
            >
                <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-violet-400" />
                    <span className="font-bold text-white text-sm">바이럴 가이드</span>
                    {pattern && (
                        <span className="text-[10px] px-2 py-0.5 bg-violet-500/20 rounded text-violet-300">
                            {pattern.platform}
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {/* Progress */}
                    {totalCount > 0 && (
                        <div className="flex items-center gap-1.5">
                            <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-violet-500 to-emerald-500 transition-all duration-300"
                                    style={{ width: `${completionPercent}%` }}
                                />
                            </div>
                            <span className="text-[10px] text-white/40">{completedCount}/{totalCount}</span>
                        </div>
                    )}
                    <button
                        onClick={(e) => { e.stopPropagation(); onClose(); }}
                        className="p-1 hover:bg-white/10 rounded transition-colors"
                    >
                        <X className="w-3.5 h-3.5 text-white/40" />
                    </button>
                    {collapsed ? <ChevronDown className="w-4 h-4 text-white/40" /> : <ChevronUp className="w-4 h-4 text-white/40" />}
                </div>
            </div>

            {/* Content */}
            {!collapsed && (
                <div className="p-4 space-y-4 max-h-[400px] overflow-y-auto">
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <div className="w-6 h-6 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : error && !pattern ? (
                        <div className="text-center py-6 text-red-400 text-sm">
                            <AlertTriangle className="w-6 h-6 mx-auto mb-2" />
                            {error}
                        </div>
                    ) : pattern ? (
                        <>
                            {/* Pattern Info */}
                            <div className="text-xs text-white/40 flex items-center gap-2 pb-2 border-b border-white/10">
                                <span>{pattern.pattern_id.replace(/_/g, ' ')}</span>
                                <span>•</span>
                                <span>v{pattern.revision}</span>
                            </div>

                            {/* Invariant Rules - Checklist */}
                            <div>
                                <h4 className="flex items-center gap-2 text-xs text-violet-400 font-bold mb-3">
                                    <Lightbulb className="w-3.5 h-3.5" />
                                    필수 체크리스트
                                </h4>
                                <div className="space-y-2">
                                    {Object.entries(invariantRules).map(([rule, description]) => (
                                        <label
                                            key={rule}
                                            className={`flex items-start gap-3 p-2.5 rounded-lg border cursor-pointer transition-all ${checkedRules.has(rule)
                                                ? 'bg-emerald-500/10 border-emerald-500/30'
                                                : 'bg-white/5 border-white/10 hover:border-violet-500/30'
                                                }`}
                                        >
                                            <div className="pt-0.5">
                                                <input
                                                    type="checkbox"
                                                    checked={checkedRules.has(rule)}
                                                    onChange={() => toggleRule(rule)}
                                                    className="sr-only"
                                                />
                                                <div className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${checkedRules.has(rule)
                                                    ? 'bg-emerald-500 border-emerald-500'
                                                    : 'border-white/30'
                                                    }`}>
                                                    {checkedRules.has(rule) && (
                                                        <CheckCircle2 className="w-3 h-3 text-white" />
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className={`text-xs font-medium ${checkedRules.has(rule) ? 'text-emerald-300 line-through opacity-70' : 'text-white'}`}>
                                                    {rule}
                                                </div>
                                                <div className="text-[11px] text-white/40 mt-0.5">
                                                    {String(description)}
                                                </div>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            {/* Mutation Strategy */}
                            <div>
                                <h4 className="flex items-center gap-2 text-xs text-pink-400 font-bold mb-3">
                                    <Repeat className="w-3.5 h-3.5" />
                                    변주 가능 포인트
                                </h4>
                                <div className="flex flex-wrap gap-2">
                                    {Object.entries(mutationStrategy).map(([key, val]) => {
                                        const value = val as { risk?: string; impact?: string } | string;
                                        const risk = typeof value === 'object' ? value.risk : 'unknown';
                                        const impact = typeof value === 'object' ? value.impact : '';
                                        return (
                                            <div
                                                key={key}
                                                className={`px-3 py-2 rounded-lg border text-xs ${getRiskColor(risk || '')}`}
                                            >
                                                <div className="font-medium">{key}</div>
                                                <div className="flex items-center gap-1.5 mt-1 opacity-70">
                                                    <span className="text-[10px]">{getRiskLabel(risk || '')}</span>
                                                    {impact && <span className="text-[10px]">• {impact}</span>}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Completion Message */}
                            {completionPercent === 100 && (
                                <div className="flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400 text-xs">
                                    <CheckCircle2 className="w-4 h-4" />
                                    <span className="font-medium">모든 필수 항목 체크 완료! 🎉</span>
                                </div>
                            )}

                            {/* Phase 6: Pattern Performance Stats */}
                            {performanceStats && (
                                <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                                    <div className="text-xs font-bold text-blue-400 mb-2">📊 이 패턴 성과</div>
                                    <div className="grid grid-cols-3 gap-2 text-center">
                                        <div>
                                            <div className="text-lg font-bold text-white">{performanceStats.avgViews.toLocaleString()}</div>
                                            <div className="text-[10px] text-white/50">평균 조회</div>
                                        </div>
                                        <div>
                                            <div className="text-lg font-bold text-emerald-400">{performanceStats.successRate}</div>
                                            <div className="text-[10px] text-white/50">성공률</div>
                                        </div>
                                        <div>
                                            <div className="text-lg font-bold text-white">{performanceStats.totalSubmissions}</div>
                                            <div className="text-[10px] text-white/50">제출 수</div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Phase 6: Related O2O Campaigns */}
                            {relatedCampaigns.length > 0 && (
                                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                                    <div className="text-xs font-bold text-amber-400 mb-2">🎁 참여 가능한 캠페인</div>
                                    <div className="space-y-2">
                                        {relatedCampaigns.map((campaign: any) => (
                                            <a
                                                key={campaign.id}
                                                href={`/o2o?campaign=${campaign.id}`}
                                                className="block p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
                                            >
                                                <div className="text-xs font-medium text-white">{campaign.title}</div>
                                                <div className="text-[10px] text-white/50">
                                                    {campaign.brand_name} • {campaign.campaign_type}
                                                </div>
                                            </a>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Download Guide Button */}
                            <button
                                onClick={() => setShowGuideCard(true)}
                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-500 hover:to-pink-500 rounded-lg text-white text-xs font-bold transition-all"
                            >
                                <Download className="w-4 h-4" />
                                가이드 저장/인쇄
                            </button>

                            {/* P2: Submit Video Section */}
                            <div className="pt-3 mt-3 border-t border-white/10">
                                {!showSubmitForm ? (
                                    <button
                                        onClick={() => setShowSubmitForm(true)}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/20 rounded-lg text-emerald-400 text-xs font-bold transition-all"
                                    >
                                        <Upload className="w-4 h-4" />
                                        촬영 완료! 영상 제출하기
                                    </button>
                                ) : (
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between text-xs">
                                            <span className="text-emerald-400 font-bold">📹 영상 제출</span>
                                            <button
                                                onClick={() => setShowSubmitForm(false)}
                                                className="text-white/40 hover:text-white/60"
                                            >
                                                취소
                                            </button>
                                        </div>

                                        <input
                                            type="url"
                                            value={videoUrl}
                                            onChange={(e) => setVideoUrl(e.target.value)}
                                            placeholder="TikTok/Instagram/YouTube URL"
                                            className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg text-xs text-white placeholder-white/30 focus:outline-none focus:border-emerald-500/50"
                                        />

                                        <textarea
                                            value={creatorNotes}
                                            onChange={(e) => setCreatorNotes(e.target.value)}
                                            placeholder="변주한 부분 메모 (선택)"
                                            rows={2}
                                            className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg text-xs text-white placeholder-white/30 focus:outline-none focus:border-emerald-500/50 resize-none"
                                        />

                                        <button
                                            onClick={async () => {
                                                if (!videoUrl.trim() || !patternId) return;
                                                setSubmitting(true);
                                                setSubmitMessage(null);
                                                try {
                                                    // Detect platform from URL
                                                    const platform = videoUrl.includes('tiktok') ? 'tiktok'
                                                        : videoUrl.includes('instagram') ? 'instagram'
                                                            : 'youtube';

                                                    const token = api.getToken();
                                                    const headers: HeadersInit = {
                                                        'Content-Type': 'application/json',
                                                        ...(token ? { Authorization: `Bearer ${token}` } : {}),
                                                    };

                                                    const response = await fetch('/api/v1/creator/submissions', {
                                                        method: 'POST',
                                                        headers,
                                                        body: JSON.stringify({
                                                            pattern_id: patternId,
                                                            video_url: videoUrl,
                                                            platform,
                                                            creator_notes: creatorNotes || null,
                                                            invariant_checklist: Object.fromEntries(
                                                                Array.from(checkedRules).map(rule => [rule, true])
                                                            ),
                                                        })
                                                    });

                                                    if (!response.ok) {
                                                        const err = await response.json();
                                                        throw new Error(err.detail || '제출 실패');
                                                    }

                                                    const data = await response.json();
                                                    setSubmitMessage({ type: 'success', text: data.message || '제출 완료!' });
                                                    setVideoUrl('');
                                                    setCreatorNotes('');
                                                    setShowSubmitForm(false);
                                                } catch (e: any) {
                                                    setSubmitMessage({ type: 'error', text: e.message });
                                                } finally {
                                                    setSubmitting(false);
                                                }
                                            }}
                                            disabled={!videoUrl.trim() || submitting}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-500/30 disabled:cursor-not-allowed rounded-lg text-white text-xs font-bold transition-all"
                                        >
                                            {submitting ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Send className="w-4 h-4" />
                                            )}
                                            {submitting ? '제출 중...' : '지표 추적 시작'}
                                        </button>
                                    </div>
                                )}

                                {submitMessage && (
                                    <div className={`mt-2 p-2 rounded-lg text-xs ${submitMessage.type === 'success'
                                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                        : 'bg-red-500/10 text-red-400 border border-red-500/30'
                                        }`}>
                                        {submitMessage.text}
                                    </div>
                                )}
                            </div>
                        </>
                    ) : null}
                </div>
            )}

            {/* Viral Guide Card Modal */}
            {showGuideCard && pattern && (
                <ViralGuideCard
                    pattern={pattern}
                    onClose={() => setShowGuideCard(false)}
                />
            )}
        </div>
    );
}
