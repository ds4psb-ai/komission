"use client";

import { useTranslations } from 'next-intl';

/**
 * ConsentDemo - 동의 UI 테스트 페이지
 */
import React, { useState, useEffect, useRef } from 'react';
import { useConsent } from '@/contexts/ConsentContext';
import { Database, RefreshCw, AlertCircle } from 'lucide-react';

export default function ConsentDemoPage() {
    const { requestConsent, executeWithConsent, consentHistory, isPending } = useConsent();
    const t = useTranslations('pages.session.consentDemo');
    const [result, setResult] = useState<string | null>(null);
    const isMountedRef = useRef(true);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

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

        if (isMountedRef.current) {
            if (success) {
                setResult(`${t('results.sourcePackComplete')}: ${JSON.stringify(success)}`);
            } else {
                setResult(t('results.cancelled'));
            }
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

        if (isMountedRef.current) {
            if (success) {
                setResult(`${t('results.vdgQueued')}: ${JSON.stringify(success)}`);
            } else {
                setResult(t('results.cancelled'));
            }
        }
    };

    // 커스텀 동의 요청
    const handleCustomConsent = async () => {
        const consented = await requestConsent('custom_action', {
            name: t('customConsent.name'),
            description: t('customConsent.requestDesc'),
            type: 'external_api',
            details: ['외부 서비스에 데이터 전송', '응답 시간은 상황에 따라 다름'],
        });

        if (isMountedRef.current) {
            if (consented) {
                setResult(`${t('customConsent.name')}: ${t('results.consented')}`);
            } else {
                setResult(`${t('customConsent.name')}: ${t('results.rejected')}`);
            }
        }
    };

    return (
        <div className="min-h-screen pb-24">
            <main className="max-w-lg mx-auto px-4 py-8 space-y-8">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">
                        {t('title')}
                    </h1>
                    <p className="text-white/60">
                        {t('subtitle')}
                    </p>
                </div>

                {/* Test Buttons */}
                <div className="space-y-4">
                    <h2 className="text-sm font-medium text-white/40 uppercase tracking-wider">
                        {t('requiresConsent')}
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
                            <p className="font-medium text-white">{t('sourcePack.title')}</p>
                            <p className="text-sm text-white/50">{t('sourcePack.description')}</p>
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
                            <p className="font-medium text-white">{t('vdgReanalyze.title')}</p>
                            <p className="text-sm text-white/50">{t('vdgReanalyze.description')}</p>
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
                            <p className="font-medium text-white">{t('customConsent.title')}</p>
                            <p className="text-sm text-white/50">{t('customConsent.description')}</p>
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
                            {t('history.title')}
                        </h2>
                        <div className="space-y-2">
                            {consentHistory.slice(-5).reverse().map((item, i) => (
                                <div
                                    key={i}
                                    className="flex items-center justify-between px-4 py-2 rounded-lg bg-white/5"
                                >
                                    <span className="text-sm text-white/70">{item.actionId}</span>
                                    <span className={`text-xs ${item.consented ? 'text-green-400' : 'text-red-400'}`}>
                                        {item.consented ? t('history.consent') : t('history.reject')}
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
