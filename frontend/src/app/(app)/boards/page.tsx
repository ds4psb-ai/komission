'use client';

import { useEffect, useState, useRef } from 'react';
import { api, EvidenceBoard } from '@/lib/api';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Plus, Target, Trophy, FileText } from 'lucide-react';

// Mock data for demo/dev
const MOCK_BOARDS: EvidenceBoard[] = [
    {
        id: "demo-1",
        title: "Q1 Hook 실험 보드",
        description: "질문형 Hook vs 충격형 Hook 성과 비교 실험. TikTok 및 Instagram Reels에서 동일 컨텐츠로 A/B 테스트 진행 중.",
        owner_id: "user-1",
        kpi_target: "Retention > 50%",
        conclusion: null,
        winner_item_id: null,
        status: "ACTIVE",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        concluded_at: null,
    },
    {
        id: "demo-2",
        title: "성수 팝업 캠페인",
        description: "오프라인 제휴 컨텐츠 테스트. 방문 인증 vs 제품 언박싱 두 가지 포맷 비교.",
        owner_id: "user-1",
        kpi_target: "Views > 100K",
        conclusion: "방문 인증 컨텐츠가 2.3배 높은 engagement 기록",
        winner_item_id: "item-a",
        status: "CONCLUDED",
        created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        concluded_at: new Date().toISOString(),
    },
    {
        id: "demo-3",
        title: "음식 ASMR 테스트",
        description: "불닭볶음면 챌린지 변주 실험. 오디오 유무에 따른 시청 시간 차이 분석.",
        owner_id: "user-1",
        kpi_target: "Watch Time > 30s",
        conclusion: null,
        winner_item_id: null,
        status: "DRAFT",
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        concluded_at: null,
    },
];

export default function EvidenceBoardsPage() {
    const [boards, setBoards] = useState<EvidenceBoard[]>([]);
    const [loading, setLoading] = useState(true);
    const isMountedRef = useRef(true);

    useEffect(() => {
        loadBoards();
    }, []);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const loadBoards = async () => {
        try {
            const data = await api.listBoards();
            if (!isMountedRef.current) return;
            setBoards(data.length > 0 ? data : MOCK_BOARDS);
        } catch (e) {
            console.warn("API failed, using mock data:", e);
            if (isMountedRef.current) {
                setBoards(MOCK_BOARDS);
            }
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    };

    return (
        <div className="p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white">
                            실험 보드
                        </h1>
                        <p className="text-white/50 mt-2">
                            KPI 기반 콘텐츠 실험을 관리하고 우승자를 결정하세요
                        </p>
                    </div>
                    <button className="px-4 py-2.5 bg-gradient-to-r from-violet-600 to-pink-600 rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center gap-2 text-white">
                        <Plus className="w-4 h-4" />
                        <span>새 보드</span>
                    </button>
                </div>

                {/* Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-48 rounded-xl bg-white/5 border border-white/10" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {boards.map((board) => (
                            <Link href={`/boards/${board.id}`} key={board.id}>
                                <motion.div
                                    className="bg-white/5 backdrop-blur-sm border border-white/10 p-6 rounded-xl hover:border-violet-500/50 cursor-pointer h-full flex flex-col transition-all"
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    <div className="flex justify-between items-start mb-4">
                                        <StatusBadge status={board.status} />
                                        {board.winner_item_id && (
                                            <span className="text-xs bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded-full border border-yellow-500/30 flex items-center gap-1">
                                                <Trophy className="w-3 h-3" />
                                                우승자
                                            </span>
                                        )}
                                    </div>

                                    <h3 className="text-lg font-bold mb-2 text-white">{board.title}</h3>
                                    <p className="text-sm text-white/40 mb-6 flex-grow line-clamp-2">
                                        {board.description || "설명 없음"}
                                    </p>

                                    <div className="border-t border-white/10 pt-4 flex justify-between items-center text-sm">
                                        <div className="flex items-center gap-2 text-cyan-300">
                                            <FileText className="w-3.5 h-3.5" />
                                            <span>3개 아이템</span>
                                        </div>
                                        {board.kpi_target && (
                                            <div className="flex items-center gap-1.5 text-white/40">
                                                <Target className="w-3.5 h-3.5" />
                                                <span>{board.kpi_target}</span>
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const config: Record<string, { bg: string; text: string; label: string }> = {
        DRAFT: { bg: "bg-gray-500/20", text: "text-gray-300", label: "초안" },
        ACTIVE: { bg: "bg-green-500/20", text: "text-green-300", label: "진행중" },
        CONCLUDED: { bg: "bg-blue-500/20", text: "text-blue-300", label: "완료" },
    };
    const { bg, text, label } = config[status] || config.DRAFT;

    return (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border border-white/10 ${bg} ${text}`}>
            {label}
        </span>
    );
}
