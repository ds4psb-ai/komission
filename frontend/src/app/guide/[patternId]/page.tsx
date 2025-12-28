'use client';

/**
 * Creator Guide Page - Simple Pattern Guidance View
 * 
 * Navigation: /guide/[patternId]
 * Shows minimal creator guide for a pattern
 */

import { useParams, useRouter } from 'next/navigation';
import { SimpleCreatorGuide } from '@/components/SimpleCreatorGuide';
import { ArrowLeft } from 'lucide-react';

export default function CreatorGuidePage() {
    const params = useParams();
    const router = useRouter();
    const patternId = params.patternId as string;

    const handleApply = () => {
        // Navigate to O2O or Canvas with this pattern
        router.push(`/canvas?pattern=${patternId}`);
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
            {/* Header */}
            <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-lg border-b border-white/5">
                <div className="max-w-lg mx-auto px-4 py-3 flex items-center gap-3">
                    <button
                        onClick={() => router.back()}
                        className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5 text-white/60" />
                    </button>
                    <h1 className="text-sm font-medium text-white">촬영 가이드</h1>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-lg mx-auto px-4 py-8">
                {patternId ? (
                    <SimpleCreatorGuide
                        patternId={patternId}
                        onApply={handleApply}
                    />
                ) : (
                    <div className="text-center text-white/50 py-20">
                        패턴 ID가 필요합니다
                    </div>
                )}
            </main>
        </div>
    );
}
