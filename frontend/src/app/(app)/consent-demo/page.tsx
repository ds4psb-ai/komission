"use client";

/**
 * ConsentDemo - 동의 UI 테스트 페이지
 */
import React, { useState } from 'react';
import { useConsent, MCP_TOOLS } from '@/contexts/ConsentContext';
import { Sparkles, Database, RefreshCw, AlertCircle } from 'lucide-react';

export default function ConsentDemoPage() {
    const { requestConsent, executeWithConsent, consentHistory, isPending } = useConsent();
    const [result, setResult] = useState<string | null>(null);

    // 동의 후 직접 실행
    const handleGenerateSourcePack = async () => {
        const success = await executeWithConsent(
            'generate_source_pack',
            async () => {
                // 실제로는 API 호출
                await new Promise(r => setTimeout(r, 1500));
                return { packId: 'pack_123', status: 'created' };
            }
        );

        if (success) {
            setResult(`Source Pack 생성 완료: ${JSON.stringify(success)}`);
        } else {
            setResult('사용자가 취소했습니다.');
        }
    };

    // VDG 재분석 요청
    const handleReanalyzeVDG = async () => {
        const success = await executeWithConsent(
            'reanalyze_vdg',
            async () => {
                await new Promise(r => setTimeout(r, 2000));
                return { status: 'queued', estimatedTime: '5분' };
            }
        );

        if (success) {
            setResult(`VDG 재분석 요청됨: ${JSON.stringify(success)}`);
        } else {
            setResult('사용자가 취소했습니다.');
        }
    };

    // 커스텀 동의 요청
    const handleCustomConsent = async () => {
        const consented = await requestConsent('custom_action', {
            name: '커스텀 작업',
            description: '이것은 커스텀 동의 요청 예시입니다.',
            type: 'external_api',
            details: ['외부 서비스에 데이터 전송', '응답 시간은 상황에 따라 다름'],
        });

        if (consented) {
            setResult('커스텀 작업: 동의함');
        } else {
            setResult('커스텀 작업: 거부함');
        }
    };

    return (
        <div className="min-h-screen pb-24">
            <main className="max-w-lg mx-auto px-4 py-8 space-y-8">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">
                        동의 UI 데모
                    </h1>
                    <p className="text-white/60">
                        MCP Tools 실행 전 사용자 동의 요청 테스트
                    </p>
                </div>

                {/* Test Buttons */}
                <div className="space-y-4">
                    <h2 className="text-sm font-medium text-white/40 uppercase tracking-wider">
                        동의 필요 작업
                    </h2>

                    <button
                        onClick={handleGenerateSourcePack}
                        disabled={isPending}
                        className="w-full flex items-center gap-3 px-5 py-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all disabled:opacity-50"
                    >
                        <div className="p-2 rounded-lg bg-blue-500/20">
                            <Database className="w-5 h-5 text-blue-400" />
                        </div>
                        <div className="text-left">
                            <p className="font-medium text-white">Source Pack 생성</p>
                            <p className="text-sm text-white/50">데이터 생성 필요</p>
                        </div>
                    </button>

                    <button
                        onClick={handleReanalyzeVDG}
                        disabled={isPending}
                        className="w-full flex items-center gap-3 px-5 py-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all disabled:opacity-50"
                    >
                        <div className="p-2 rounded-lg bg-amber-500/20">
                            <RefreshCw className="w-5 h-5 text-amber-400" />
                        </div>
                        <div className="text-left">
                            <p className="font-medium text-white">VDG 재분석</p>
                            <p className="text-sm text-white/50">비용 발생 (~$0.05-0.10)</p>
                        </div>
                    </button>

                    <button
                        onClick={handleCustomConsent}
                        disabled={isPending}
                        className="w-full flex items-center gap-3 px-5 py-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all disabled:opacity-50"
                    >
                        <div className="p-2 rounded-lg bg-purple-500/20">
                            <AlertCircle className="w-5 h-5 text-purple-400" />
                        </div>
                        <div className="text-left">
                            <p className="font-medium text-white">커스텀 동의 요청</p>
                            <p className="text-sm text-white/50">외부 API 호출</p>
                        </div>
                    </button>
                </div>

                {/* Result */}
                {result && (
                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                        <p className="text-sm text-white/70">{result}</p>
                    </div>
                )}

                {/* Consent History */}
                {consentHistory.length > 0 && (
                    <div className="space-y-3">
                        <h2 className="text-sm font-medium text-white/40 uppercase tracking-wider">
                            동의 이력
                        </h2>
                        <div className="space-y-2">
                            {consentHistory.slice(-5).reverse().map((item, i) => (
                                <div
                                    key={i}
                                    className="flex items-center justify-between px-4 py-2 rounded-lg bg-white/5"
                                >
                                    <span className="text-sm text-white/70">{item.actionId}</span>
                                    <span className={`text-xs ${item.consented ? 'text-green-400' : 'text-red-400'}`}>
                                        {item.consented ? '동의' : '거부'}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
