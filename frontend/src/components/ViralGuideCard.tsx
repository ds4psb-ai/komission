'use client';

/**
 * ViralGuideCard - P1 Downloadable Guide for Creators
 * 
 * 체험단/크리에이터가 촬영 시 참고할 수 있는 바이럴 가이드
 * - 인쇄 가능한 디자인
 * - 이미지 다운로드 지원
 */

import { useState, useRef, useEffect } from 'react';
import { PatternLibraryItem } from '@/lib/api';
import { Download, Printer, Share2, CheckCircle2, AlertTriangle, Lightbulb, Repeat, Sparkles } from 'lucide-react';
import html2canvas from 'html2canvas';

interface ViralGuideCardProps {
    pattern: PatternLibraryItem;
    onClose?: () => void;
}

export function ViralGuideCard({ pattern, onClose }: ViralGuideCardProps) {
    const cardRef = useRef<HTMLDivElement>(null);
    const [downloading, setDownloading] = useState(false);
    const isMountedRef = useRef(true);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const handleDownload = async () => {
        if (!cardRef.current) return;

        setDownloading(true);
        try {
            const canvas = await html2canvas(cardRef.current, {
                backgroundColor: '#0a0a0a',
                scale: 2, // Higher resolution
            });

            const link = document.createElement('a');
            link.download = `viral-guide-${pattern.pattern_id}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();
        } catch (e) {
            console.error('Download failed:', e);
            alert('다운로드 실패. 다시 시도해주세요.');
        } finally {
            if (isMountedRef.current) {
                setDownloading(false);
            }
        }
    };

    const handlePrint = () => {
        window.print();
    };

    const handleShare = async () => {
        const shareData = {
            title: `바이럴 가이드: ${pattern.pattern_id}`,
            text: `${pattern.platform} ${pattern.category} 촬영 가이드`,
            url: window.location.href,
        };

        if (navigator.share) {
            try {
                await navigator.share(shareData);
            } catch (e) {
                console.log('Share cancelled');
            }
        } else {
            // Fallback: copy link
            try {
                if (!navigator.clipboard?.writeText) {
                    alert('클립보드를 사용할 수 없습니다. 주소를 직접 복사해주세요.');
                    return;
                }
                await navigator.clipboard.writeText(window.location.href);
                alert('링크가 복사되었습니다!');
            } catch (e) {
                console.error('Clipboard write failed:', e);
                alert('링크 복사에 실패했습니다.');
            }
        }
    };

    const invariantRules = pattern.invariant_rules || {};
    const mutationStrategy = pattern.mutation_strategy || {};

    const getRiskBadge = (risk: string) => {
        switch (risk) {
            case 'low': return { label: '안전', color: 'bg-emerald-500' };
            case 'medium': return { label: '주의', color: 'bg-amber-500' };
            case 'high': return { label: '위험', color: 'bg-red-500' };
            default: return { label: risk, color: 'bg-gray-500' };
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 print:p-0 print:bg-white">
            <div className="max-w-lg w-full">
                {/* Action Buttons */}
                <div className="flex justify-end gap-2 mb-4 print:hidden">
                    <button
                        onClick={handleShare}
                        className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white transition-colors"
                    >
                        <Share2 className="w-4 h-4" />
                        공유
                    </button>
                    <button
                        onClick={handlePrint}
                        className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white transition-colors"
                    >
                        <Printer className="w-4 h-4" />
                        인쇄
                    </button>
                    <button
                        onClick={handleDownload}
                        disabled={downloading}
                        className="flex items-center gap-2 px-4 py-2 bg-violet-500 hover:bg-violet-600 rounded-lg text-sm text-white transition-colors disabled:opacity-50"
                    >
                        <Download className={`w-4 h-4 ${downloading ? 'animate-bounce' : ''}`} />
                        {downloading ? '저장 중...' : '이미지 저장'}
                    </button>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-white/60 transition-colors"
                        >
                            닫기
                        </button>
                    )}
                </div>

                {/* Printable Card */}
                <div
                    ref={cardRef}
                    className="bg-gradient-to-br from-[#0f0f0f] via-[#1a1a2e] to-[#16213e] rounded-2xl overflow-hidden border border-white/10 print:border-gray-300"
                >
                    {/* Header */}
                    <div className="bg-gradient-to-r from-violet-600 to-pink-600 p-6 text-white">
                        <div className="flex items-center gap-2 text-xs opacity-80 mb-2">
                            <Sparkles className="w-4 h-4" />
                            <span>KOMISSION 바이럴 가이드</span>
                        </div>
                        <h1 className="text-2xl font-black">
                            {pattern.pattern_id.replace(/_/g, ' ').toUpperCase()}
                        </h1>
                        <div className="flex gap-2 mt-3">
                            <span className="px-2 py-1 bg-white/20 rounded text-xs font-medium">
                                {pattern.platform}
                            </span>
                            <span className="px-2 py-1 bg-white/20 rounded text-xs font-medium">
                                {pattern.category}
                            </span>
                            <span className="px-2 py-1 bg-white/20 rounded text-xs font-medium">
                                {pattern.temporal_phase}
                            </span>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="p-6 space-y-6">
                        {/* Invariant Rules - Must Follow */}
                        <div>
                            <h2 className="flex items-center gap-2 text-sm font-bold text-white mb-4">
                                <Lightbulb className="w-4 h-4 text-yellow-400" />
                                <span>✅ 반드시 지켜야 할 것</span>
                            </h2>
                            <div className="space-y-3">
                                {Object.entries(invariantRules).map(([rule, description], idx) => (
                                    <div
                                        key={rule}
                                        className="flex gap-3 p-3 bg-white/5 rounded-lg border border-white/10"
                                    >
                                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-violet-500/20 flex items-center justify-center text-violet-400 text-xs font-bold">
                                            {idx + 1}
                                        </div>
                                        <div>
                                            <div className="text-sm font-medium text-white">{rule}</div>
                                            <div className="text-xs text-white/50 mt-1">{String(description)}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Mutation Strategy - Can Modify */}
                        <div>
                            <h2 className="flex items-center gap-2 text-sm font-bold text-white mb-4">
                                <Repeat className="w-4 h-4 text-pink-400" />
                                <span>🎨 변주 가능한 포인트</span>
                            </h2>
                            <div className="grid grid-cols-2 gap-2">
                                {Object.entries(mutationStrategy).map(([key, val]) => {
                                    const value = val as { risk?: string; impact?: string } | string;
                                    const risk = typeof value === 'object' ? value.risk : 'unknown';
                                    const impact = typeof value === 'object' ? value.impact : '';
                                    const badge = getRiskBadge(risk || '');

                                    return (
                                        <div
                                            key={key}
                                            className="p-3 bg-white/5 rounded-lg border border-white/10"
                                        >
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="text-xs font-medium text-white">{key}</span>
                                                <span className={`px-1.5 py-0.5 rounded text-[10px] text-white ${badge.color}`}>
                                                    {badge.label}
                                                </span>
                                            </div>
                                            {impact && (
                                                <div className="text-[11px] text-emerald-400">
                                                    예상 효과: {impact}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="pt-4 border-t border-white/10 text-center">
                            <p className="text-[10px] text-white/30">
                                Generated by KOMISSION Pattern Engine v{pattern.revision}
                            </p>
                            <p className="text-[10px] text-white/30 mt-1">
                                {new Date().toLocaleDateString('ko-KR')}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
