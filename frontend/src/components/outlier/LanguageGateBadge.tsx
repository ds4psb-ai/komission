'use client';

import { Globe, AlertCircle } from 'lucide-react';

interface LanguageGateBadgeProps {
    lang: string;  // 'ko', 'en', 'ja', etc.
    hasTranslation?: boolean;
}

/**
 * LanguageGateBadge - 언어 적합성 게이트 표시
 * 
 * - 한국어 → 표시 안 함 (기본)
 * - 영어 + 번역 → "🌐 영어 • 번역제공"
 * - 영어 - 번역 → "⚠️ 영어 • 자동생성"
 * - 기타 → 경고 표시
 */
export function LanguageGateBadge({ lang, hasTranslation = false }: LanguageGateBadgeProps) {
    // 한국어는 배지 표시 안 함
    if (lang === 'ko') return null;

    const langNames: Record<string, string> = {
        en: '영어',
        ja: '일본어',
        zh: '중국어',
        es: '스페인어',
    };

    const displayLang = langNames[lang] || lang.toUpperCase();

    if (lang === 'en' && hasTranslation) {
        return (
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] text-blue-400">
                <Globe className="w-3 h-3" />
                <span>{displayLang}</span>
                <span className="opacity-50">•</span>
                <span className="text-blue-300">번역제공</span>
            </div>
        );
    }

    if (lang === 'en') {
        return (
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-400">
                <AlertCircle className="w-3 h-3" />
                <span>{displayLang}</span>
                <span className="opacity-50">•</span>
                <span className="text-amber-300">자동생성</span>
            </div>
        );
    }

    // 기타 언어
    return (
        <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-[10px] text-white/50">
            <Globe className="w-3 h-3" />
            <span>{displayLang}</span>
        </div>
    );
}

export default LanguageGateBadge;
