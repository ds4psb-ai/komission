// frontend/src/app/remix/[nodeId]/genealogy/page.tsx
"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";

// Dynamic import for heavy genealogy component
const GenealogyWidget = dynamic(
    () => import("@/components/GenealogyWidget").then((m) => ({ default: m.GenealogyWidget })),
    {
        ssr: false,
        loading: () => (
            <div className="glass-panel p-6 rounded-2xl animate-pulse h-96 flex items-center justify-center">
                <span className="text-white/40">계보 로딩 중...</span>
            </div>
        ),
    }
);

export default function GenealogyPage() {
    const params = useParams();
    const nodeId = params.nodeId as string;

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <h1 className="text-2xl font-black flex items-center gap-3">
                🌳 밈 계보
                <span className="text-xs font-bold bg-pink-500 px-2 py-1 rounded text-white">PRO</span>
            </h1>

            {/* Genealogy Tree */}
            <GenealogyWidget nodeId={nodeId} depth={3} layer="fork" />

            {/* Mutation History */}
            <div className="glass-panel p-6 rounded-2xl">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                    🔀 변이 히스토리
                </h2>
                <div className="space-y-4">
                    <div className="flex items-center gap-4 p-4 bg-white/5 rounded-xl border border-white/10">
                        <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                            <span className="text-emerald-400">1</span>
                        </div>
                        <div className="flex-1">
                            <div className="font-bold text-white">Original Source</div>
                            <div className="text-xs text-white/50">Master Layer • 1.2M views</div>
                        </div>
                        <span className="text-xs text-emerald-400 font-bold">MASTER</span>
                    </div>

                    <div className="flex items-center gap-4 p-4 bg-white/5 rounded-xl border border-violet-500/20">
                        <div className="w-10 h-10 rounded-full bg-violet-500/20 flex items-center justify-center">
                            <span className="text-violet-400">2</span>
                        </div>
                        <div className="flex-1">
                            <div className="font-bold text-white">현재 노드</div>
                            <div className="text-xs text-white/50">Fork Layer • +89% 성장</div>
                        </div>
                        <span className="text-xs text-violet-400 font-bold">CURRENT</span>
                    </div>
                </div>
            </div>

            {/* Fork Statistics */}
            <div className="grid md:grid-cols-3 gap-4">
                <div className="glass-panel p-6 rounded-2xl text-center">
                    <div className="text-3xl font-black text-white mb-1">12</div>
                    <div className="text-xs text-white/50">총 Fork 수</div>
                </div>
                <div className="glass-panel p-6 rounded-2xl text-center">
                    <div className="text-3xl font-black text-emerald-400 mb-1">+89%</div>
                    <div className="text-xs text-white/50">평균 성장률</div>
                </div>
                <div className="glass-panel p-6 rounded-2xl text-center">
                    <div className="text-3xl font-black text-violet-400 mb-1">Layer 2</div>
                    <div className="text-xs text-white/50">현재 계층</div>
                </div>
            </div>
        </div>
    );
}
