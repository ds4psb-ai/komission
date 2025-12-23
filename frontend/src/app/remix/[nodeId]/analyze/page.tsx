// frontend/src/app/remix/[nodeId]/analyze/page.tsx
"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";

// Dynamic import for heavy component
const PatternConfidenceChart = dynamic(
    () => import("@/components/PatternConfidenceChart").then((m) => ({ default: m.PatternConfidenceChart })),
    {
        ssr: false,
        loading: () => (
            <div className="glass-panel p-6 rounded-2xl animate-pulse h-64 flex items-center justify-center">
                <span className="text-white/40">차트 로딩 중...</span>
            </div>
        ),
    }
);

export default function AnalyzePage() {
    const params = useParams();
    const nodeId = params.nodeId as string;

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <h1 className="text-2xl font-black flex items-center gap-3">
                🧬 AI 비디오 DNA
                <span className="text-xs font-bold bg-violet-500 px-2 py-1 rounded text-white">PRO</span>
            </h1>

            {/* Pattern Confidence Chart */}
            <div className="glass-panel p-6 rounded-2xl">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                    📊 패턴 신뢰도
                </h2>
                <PatternConfidenceChart />
            </div>

            {/* AI Analysis Results */}
            <div className="grid md:grid-cols-2 gap-6">
                <div className="glass-panel p-6 rounded-2xl">
                    <h3 className="text-sm font-bold text-white/60 uppercase tracking-wider mb-4">바이럴 패턴</h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-white/80">Hook 강도</span>
                            <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-violet-500 to-pink-500 w-[85%]" />
                            </div>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-white/80">엔게이지먼트</span>
                            <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 w-[72%]" />
                            </div>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-white/80">공유성</span>
                            <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-orange-500 to-yellow-500 w-[68%]" />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="glass-panel p-6 rounded-2xl">
                    <h3 className="text-sm font-bold text-white/60 uppercase tracking-wider mb-4">추천 해시태그</h3>
                    <div className="flex flex-wrap gap-2">
                        {["#챌린지", "#viral", "#fyp", "#리믹스", "#틱톡"].map((tag) => (
                            <span
                                key={tag}
                                className="px-3 py-1 bg-cyan-500/20 text-cyan-300 text-sm rounded-full border border-cyan-500/30"
                            >
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
            </div>

            {/* Claude Strategy Brief */}
            <div className="glass-panel p-6 rounded-2xl border border-violet-500/20">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                    🧠 전략 브리프
                    <span className="text-xs bg-violet-500 px-2 py-0.5 rounded text-white">Claude 3.5</span>
                </h2>
                <div className="p-4 bg-violet-500/10 rounded-xl border border-violet-500/20">
                    <p className="text-sm text-white/80 leading-relaxed">
                        이 콘텐츠는 <strong>Z세대 트렌드</strong>를 정확히 겨냥하고 있습니다.
                        첫 3초 Hook과 중반부 전환이 핵심 성공 요소입니다.
                        유사한 패턴의 리믹스는 평균 <strong>+127% 조회수 성장</strong>을 기록했습니다.
                    </p>
                </div>
            </div>
        </div>
    );
}
