'use client';

import { useTranslations } from 'next-intl';

import { useEffect, useState, use, useRef } from 'react';
import { api, EvidenceBoardDetail, BoardItem } from '@/lib/api';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowLeft, Settings, Plus, ExternalLink, X } from 'lucide-react';

// Mock data matching API type
const MOCK_ITEMS: BoardItem[] = [
    { id: "item-1", board_id: "demo-1", outlier_item_id: "out-1", remix_node_id: null, notes: "질문형 Hook 적용 버전. 3초 내 질문으로 시청자 주의 집중.", added_at: new Date().toISOString(), item_data: { title: "질문 Hook 버전 A", platform: "tiktok", source_url: "https://tiktok.com/example1" } },
    { id: "item-2", board_id: "demo-1", outlier_item_id: null, remix_node_id: "node-1", notes: "충격 Reveal 적용 버전. Before/After 구조로 시각적 반전.", added_at: new Date().toISOString(), item_data: { title: "Shock Reveal 버전 B", platform: "instagram", source_url: "https://instagram.com/example2" } },
    { id: "item-3", board_id: "demo-1", outlier_item_id: "out-2", remix_node_id: null, notes: null, added_at: new Date().toISOString(), item_data: { title: "ASMR Sound 버전 C", platform: "youtube", source_url: "https://youtube.com/example3" } },
];

const MOCK_BOARD: EvidenceBoardDetail = {
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
    items: MOCK_ITEMS,
    item_count: 3,
};

export default function BoardDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const unwrappedParams = use(params);
    const t = useTranslations('pages.boards.detail');
    const [board, setBoard] = useState<EvidenceBoardDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const isMountedRef = useRef(true);

    useEffect(() => {
        const loadBoard = async () => {
            try {
                const data = await api.getBoard(unwrappedParams.id);
                if (!isMountedRef.current) return;
                setBoard(data);
            } catch (e) {
                console.warn("Board API failed, using mock:", e);
                if (isMountedRef.current) {
                    setBoard({ ...MOCK_BOARD, id: unwrappedParams.id });
                }
            } finally {
                if (isMountedRef.current) {
                    setLoading(false);
                }
            }
        };
        loadBoard();
    }, [unwrappedParams.id]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    if (loading) return <div className="min-h-screen flex items-center justify-center text-white/50">{t('loading')}</div>;
    if (!board) return <div className="min-h-screen flex items-center justify-center text-white/50">{t('notFound')}</div>;

    const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
        DRAFT: { bg: "bg-gray-500/20", text: "text-gray-300", label: t('status.draft') },
        ACTIVE: { bg: "bg-green-500/20", text: "text-green-300", label: t('status.active') },
        CONCLUDED: { bg: "bg-blue-500/20", text: "text-blue-300", label: t('status.concluded') },
    };
    const status = statusConfig[board.status] || statusConfig.DRAFT;

    return (
        <div>
            {/* Sub Header */}
            <header className="h-14 border-b border-white/10 bg-black/40 backdrop-blur-sm flex items-center px-6 justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/boards" className="text-white/50 hover:text-white transition-colors flex items-center gap-1">
                        <ArrowLeft className="w-4 h-4" />
                        {t('back')}
                    </Link>
                    <div className="h-5 w-px bg-white/10" />
                    <h1 className="font-bold">{board.title}</h1>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${status.bg} ${status.text}`}>
                        {status.label}
                    </span>
                </div>
                <div className="flex gap-2">
                    <button className="px-3 py-1.5 text-sm bg-white/5 hover:bg-white/10 rounded-md border border-white/10 transition-colors flex items-center gap-1.5">
                        <Settings className="w-3.5 h-3.5" />
                        {t('settings')}
                    </button>
                    <button className="px-3 py-1.5 text-sm bg-violet-600 hover:bg-violet-500 rounded-md transition-colors flex items-center gap-1.5">
                        <Plus className="w-3.5 h-3.5" />
                        {t('addItem')}
                    </button>
                </div>
            </header>

            <div className="p-6 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
                {/* Sidebar */}
                <aside className="space-y-4">
                    <div className="bg-white/5 border border-white/10 p-5 rounded-xl space-y-4">
                        <div>
                            <label className="text-xs font-bold text-white/40 uppercase tracking-wider">{t('sidebar.kpiTarget')}</label>
                            <div className="text-lg font-mono text-cyan-300 mt-1">{board.kpi_target || t('sidebar.notSet')}</div>
                        </div>
                        <div>
                            <label className="text-xs font-bold text-white/40 uppercase tracking-wider">{t('sidebar.description')}</label>
                            <p className="text-sm text-gray-300 mt-1 leading-relaxed">
                                {board.description || t('sidebar.noDescription')}
                            </p>
                        </div>
                        <div>
                            <label className="text-xs font-bold text-white/40 uppercase tracking-wider">{t('sidebar.conclusion')}</label>
                            {board.conclusion ? (
                                <p className="text-sm text-yellow-100 bg-yellow-500/10 p-3 rounded mt-1 border border-yellow-500/20">
                                    {board.conclusion}
                                </p>
                            ) : (
                                <p className="text-sm text-gray-500 italic mt-1">{t('sidebar.conclusionPending')}</p>
                            )}
                        </div>
                    </div>

                    <div className="bg-white/5 border border-white/10 p-5 rounded-xl">
                        <h3 className="font-bold text-sm mb-3">{t('stats.title')}</h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-white/40">{t('stats.totalItems')}</span>
                                <span>{board.items?.length || 0}{t('stats.count')}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-white/40">{t('stats.createdAt')}</span>
                                <span>{new Date(board.created_at).toLocaleDateString('ko-KR')}</span>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <div className="space-y-4">
                    <div className="flex justify-between items-end">
                        <h2 className="text-xl font-bold">{t('experiments.title')}</h2>
                        <div className="text-sm text-white/40">
                            {board.items?.length || 0}{t('experiments.comparing')}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {board.items?.map((item, idx) => (
                            <motion.div
                                key={item.id}
                                className="bg-white/5 border border-white/10 p-5 rounded-xl hover:border-violet-500/50 transition-all group relative"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.05 }}
                            >
                                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button className="p-1.5 hover:text-red-400 rounded hover:bg-white/5" title={t('delete')}>
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>

                                <div className="flex items-start gap-3 mb-3">
                                    <div className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold
                                        ${item.remix_node_id ? 'bg-violet-500/20 text-violet-300' : 'bg-cyan-500/20 text-cyan-300'}`}>
                                        {item.remix_node_id ? 'R' : 'O'}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-medium truncate">{item.item_data?.title || t('noTitle')}</h4>
                                        {item.item_data?.source_url && (
                                            <a
                                                href={item.item_data.source_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-xs text-blue-400 hover:underline flex items-center gap-1"
                                            >
                                                {item.item_data?.platform || t('source')}
                                                <ExternalLink className="w-3 h-3" />
                                            </a>
                                        )}
                                    </div>
                                </div>

                                {item.notes && (
                                    <div className="bg-black/20 p-3 rounded text-sm text-gray-400 italic">
                                        {item.notes}
                                    </div>
                                )}
                            </motion.div>
                        ))}

                        {/* Add Item Placeholder */}
                        <button className="border-2 border-dashed border-white/10 rounded-xl p-6 flex flex-col items-center justify-center text-white/30 hover:text-white hover:border-white/30 transition-all min-h-[180px]">
                            <Plus className="w-6 h-6 mb-2" />
                            <span>{t('addCandidate')}</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
