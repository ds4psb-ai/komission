// frontend/src/app/remix/[nodeId]/studio/page.tsx
"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useSessionStore } from "@/stores/useSessionStore";

export default function StudioPage() {
    const params = useParams();
    const nodeId = params.nodeId as string;
    const outlier = useSessionStore((s) => s.outlier);

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <h1 className="text-2xl font-black flex items-center gap-3">
                🎛️ 스튜디오
                <span className="text-xs font-bold bg-pink-500 px-2 py-1 rounded text-white">PRO</span>
            </h1>

            {/* Canvas Link */}
            <div className="p-[2px] rounded-2xl bg-gradient-to-r from-violet-500 to-cyan-500">
                <div className="bg-[#0a0a0a] rounded-[14px] p-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <span className="text-4xl">🕸️</span>
                            <div>
                                <h2 className="text-lg font-bold text-white">캔버스 에디터</h2>
                                <p className="text-sm text-white/60">노드 기반 고급 편집 도구</p>
                            </div>
                        </div>
                        <Link
                            href={`/canvas?sourceUrl=${encodeURIComponent(outlier?.sourceUrl || '')}`}
                            className="px-6 py-3 bg-violet-500 text-white font-bold rounded-xl hover:bg-violet-400 transition-colors"
                        >
                            열기
                        </Link>
                    </div>
                </div>
            </div>

            {/* Advanced Tools */}
            <div className="grid md:grid-cols-2 gap-4">
                <div className="glass-panel p-6 rounded-2xl">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="text-2xl">🎬</span>
                        <h3 className="font-bold text-white">씬 타임라인</h3>
                    </div>
                    <p className="text-sm text-white/60 mb-4">
                        각 씬별 세부 편집 및 타이밍 조정
                    </p>
                    <button className="w-full py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white/60 cursor-not-allowed">
                        준비 중
                    </button>
                </div>

                <div className="glass-panel p-6 rounded-2xl">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="text-2xl">🎥</span>
                        <h3 className="font-bold text-white">미장센 가이드</h3>
                    </div>
                    <p className="text-sm text-white/60 mb-4">
                        프레이밍, 조명, 구도 상세 가이드
                    </p>
                    <button className="w-full py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white/60 cursor-not-allowed">
                        준비 중
                    </button>
                </div>
            </div>

            {/* Resource Downloads */}
            <div className="glass-panel p-6 rounded-2xl">
                <h2 className="text-lg font-bold mb-4">📂 리소스 다운로드</h2>
                <div className="space-y-3">
                    <button className="w-full flex items-center justify-between p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors group">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                                🎵
                            </div>
                            <div className="text-left">
                                <div className="font-bold text-white">오디오 소스</div>
                                <div className="text-xs text-white/50">원본 오디오 트랙</div>
                            </div>
                        </div>
                        <span className="text-white/30 group-hover:text-white transition-colors">↓</span>
                    </button>

                    <button className="w-full flex items-center justify-between p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors group">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-violet-500/20 flex items-center justify-center">
                                📝
                            </div>
                            <div className="text-left">
                                <div className="font-bold text-white">프롬프트 가이드</div>
                                <div className="text-xs text-white/50">AI 생성 촬영 가이드</div>
                            </div>
                        </div>
                        <span className="text-white/30 group-hover:text-white transition-colors">↓</span>
                    </button>
                </div>
            </div>
        </div>
    );
}
