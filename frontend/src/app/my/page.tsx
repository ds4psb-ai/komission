"use client";

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AppHeader } from '@/components/AppHeader';
import { api, RemixNode, RoyaltySummary, UserStats, GenealogyResponse } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { useRealTimeMetrics } from '@/hooks/useRealTimeMetrics';
import { ArrowRight } from 'lucide-react';
import { useTranslations } from 'next-intl';

interface TreeNode {
    id: string;
    title: string;
    views: number;
    forks: number;
    depth: number;
    performanceDelta?: string;
    children: TreeNode[];
}

function TreeNodeCard({ node, onSelect, selectedId }: { node: TreeNode; onSelect: (id: string) => void; selectedId: string | null }) {
    const isPositive = node.performanceDelta?.startsWith('+');
    const isSelected = selectedId === node.id;

    return (
        <div className="relative">
            <div
                onClick={() => onSelect(node.id)}
                className={`p-3 rounded-xl cursor-pointer transition-all hover:scale-105 ${isSelected
                    ? 'bg-violet-500 border-2 border-white shadow-[0_0_15px_rgba(139,92,246,0.5)] z-10 relative'
                    : node.depth === 0
                        ? 'bg-gradient-to-br from-violet-500/30 to-pink-500/30 border-2 border-violet-500/50'
                        : 'bg-white/5 border border-white/10 hover:border-white/30'
                    }`}
            >
                {/* Performance Badge */}
                {node.performanceDelta && (
                    <div className={`absolute -top-2 -right-2 px-2 py-0.5 rounded-full text-[10px] font-bold ${isPositive ? 'bg-emerald-500 text-white' : 'bg-red-500/80 text-white'
                        }`}>
                        {node.performanceDelta}
                    </div>
                )}

                <div className="text-sm font-bold text-white mb-1 truncate">{node.title}</div>
                <div className="flex items-center gap-3 text-[10px] text-white/50">
                    <span>👁️ {node.views?.toLocaleString() || 0}</span>
                    <span>🌿 {node.forks}</span>
                </div>
            </div>

            {/* Children */}
            {node.children.length > 0 && (
                <div className="ml-6 mt-2 pl-4 border-l border-white/10 space-y-2">
                    {node.children.map(child => (
                        <TreeNodeCard key={child.id} node={child} onSelect={onSelect} selectedId={selectedId} />
                    ))}
                </div>
            )}
        </div>
    );
}

export default function MyPage() {
    const router = useRouter();
    const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
    const t = useTranslations('pages.myPage');

    const [nodes, setNodes] = useState<RemixNode[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedNode, setSelectedNode] = useState<string | null>(null);

    // Genealogy State
    const [genealogyLoading, setGenealogyLoading] = useState(false);
    const [genealogyTree, setGenealogyTree] = useState<TreeNode | null>(null);

    // Royalty State
    const [royaltySummary, setRoyaltySummary] = useState<RoyaltySummary | null>(null);
    const [royaltyLoading, setRoyaltyLoading] = useState(true);

    // User Stats
    const [stats, setStats] = useState<UserStats | null>(null);
    const isMountedRef = useRef(true);

    // 🔴 Real-time WebSocket Metrics (Expert Recommendation)
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { metrics: _realTimeMetrics, isConnected: wsConnected, lastUpdate: _lastUpdate } = useRealTimeMetrics({
        userId: user?.id || null,
        enabled: isAuthenticated && !!user?.id,
    });

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push('/login?redirect=/my');
            return;
        }

        if (isAuthenticated) {
            loadMyNodes();
            loadRoyaltyData();
            loadStats();
        }
    }, [authLoading, isAuthenticated, router]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    // Load genealogy when selected node changes
    useEffect(() => {
        if (selectedNode) {
            loadGenealogy(selectedNode);
        } else if (nodes.length > 0) {
            // Select first node by default if none selected
            setSelectedNode(nodes[0].node_id);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedNode, nodes]);

    async function loadMyNodes() {
        try {
            const data = await api.listRemixNodes({ limit: 20 });
            if (!isMountedRef.current) return;
            setNodes(data);
        } catch (e) {
            console.error(e);
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    }

    async function loadStats() {
        try {
            const data = await api.getMyStats();
            if (!isMountedRef.current) return;
            setStats(data);
        } catch (e) {
            console.error('Stats load error:', e);
        }
    }

    async function loadGenealogy(nodeId: string) {
        if (isMountedRef.current) {
            setGenealogyLoading(true);
        }
        try {
            const data = await api.getRemixNodeGenealogy(nodeId);
            const tree = transformGenealogyToTree(data);
            if (!isMountedRef.current) return;
            setGenealogyTree(tree);
        } catch (e) {
            console.error("Genealogy load failed:", e);
            // Fallback: Show just the selected node
            const fallbackNode = nodes.find(n => n.node_id === nodeId);
            if (fallbackNode) {
                if (isMountedRef.current) {
                    setGenealogyTree({
                        id: fallbackNode.node_id,
                        title: fallbackNode.title,
                        views: fallbackNode.view_count,
                        forks: 0,
                        depth: 0,
                        children: []
                    });
                }
            }
        } finally {
            if (isMountedRef.current) {
                setGenealogyLoading(false);
            }
        }
    }

    function transformGenealogyToTree(data: GenealogyResponse): TreeNode {
        // Build tree from edge-based schema
        // New schema has: root, total_nodes, edges: Array<{parent, child, delta}>

        // Create a map of node IDs to their children
        const nodeChildren: Record<string, string[]> = {};
        const nodeDeltas: Record<string, string> = {};

        data.edges.forEach(edge => {
            if (!nodeChildren[edge.parent]) {
                nodeChildren[edge.parent] = [];
            }
            nodeChildren[edge.parent].push(edge.child);
            nodeDeltas[edge.child] = edge.delta;
        });

        // Build tree recursively from root
        function buildNode(nodeId: string, depth: number): TreeNode {
            const children = nodeChildren[nodeId] || [];
            return {
                id: nodeId,
                title: nodeId.substring(0, 8) + '...', // Truncated ID as title
                views: 0,
                forks: children.length,
                depth: depth,
                children: children.map(childId => buildNode(childId, depth + 1))
            };
        }

        return buildNode(data.root, 0);
    }

    async function loadRoyaltyData() {
        try {
            const summary = await api.getMyRoyalty();
            if (!isMountedRef.current) return;
            setRoyaltySummary(summary);
        } catch (e) {
            console.error('Royalty data load error:', e);
        } finally {
            if (isMountedRef.current) {
                setRoyaltyLoading(false);
            }
        }
    }

    return (
        <div className="min-h-screen bg-black text-white selection:bg-violet-500/30 selection:text-violet-200">
            <AppHeader />

            <main className="max-w-7xl mx-auto px-6 py-20">
                {/* Header - Cinematic Electric */}
                <div className="mb-16 relative">
                    <div className="absolute -top-32 -left-32 w-96 h-96 bg-[#c1ff00]/10 blur-[120px] pointer-events-none" />
                    <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8">
                        <div>
                            <h1 className="text-6xl font-black mb-6 tracking-tighter leading-none italic uppercase">
                                <span className="text-white block">MY VIRAL</span>
                                <span className="text-[#c1ff00] block drop-shadow-[0_0_15px_rgba(193,255,0,0.5)]">DASHBOARD</span>
                            </h1>
                            <div className="flex items-center gap-4">
                                <p className="text-lg text-white/60 max-w-xl font-medium">
                                    Track your AI remix performance and viral genealogy in real-time.
                                </p>
                                {/* 🔴 Real-time Connection Indicator */}
                                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-black uppercase tracking-wider ${wsConnected
                                    ? 'bg-[#c1ff00]/10 text-[#c1ff00] border border-[#c1ff00]/30 shadow-[0_0_10px_rgba(193,255,0,0.2)]'
                                    : 'bg-white/5 text-white/30 border border-white/10'
                                    }`}>
                                    <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-[#c1ff00] animate-pulse' : 'bg-white/30'}`}></span>
                                    {wsConnected ? 'LIVE SYSTEM' : 'OFFLINE'}
                                </div>
                            </div>
                        </div>

                        {/* 🆕 Expert Recommendation: Big CTA - Next Remix */}
                        <Link
                            href="/"
                            className="flex-shrink-0 group relative"
                        >
                            <div className="absolute -inset-1 bg-gradient-to-r from-[#c1ff00] to-white rounded-2xl blur opacity-20 group-hover:opacity-60 transition duration-500" />
                            <div className="relative px-8 py-5 bg-black rounded-xl border border-white/10 flex items-center gap-4 group-hover:bg-white/5 transition-colors">
                                <span className="text-3xl group-hover:rotate-12 transition-transform duration-300">⚡</span>
                                <div>
                                    <div className="font-black text-xl text-white italic uppercase tracking-tighter">FIND NEXT REMIX</div>
                                    <div className="text-xs text-[#c1ff00] font-bold uppercase tracking-wider">Avg. +89% Growth Potential</div>
                                </div>
                                <ArrowRight className="w-5 h-5 text-white/40 group-hover:text-[#c1ff00] group-hover:translate-x-2 transition-all" />
                            </div>
                        </Link>
                    </div>
                </div>

                {/* Stats Grid - Neon Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
                    {/* Creator Royalty Card */}
                    <Link
                        href="/my/royalty"
                        className="p-8 bg-black/40 backdrop-blur-xl border border-yellow-500/20 rounded-3xl relative overflow-hidden group hover:border-yellow-500/40 transition-colors block cursor-pointer"
                    >
                        <div className="absolute inset-0 bg-yellow-500/5 group-hover:bg-yellow-500/10 transition-colors" />
                        <div className="absolute top-0 right-0 p-6 opacity-20 text-6xl grayscale group-hover:grayscale-0 transition-all transform group-hover:scale-110 duration-500">💰</div>
                        <div className="relative z-10">
                            <div className="text-sm font-bold text-yellow-300 uppercase tracking-widest mb-2 flex items-center gap-2">
                                크리에이터 로열티
                                <span className="text-[10px] bg-yellow-500/20 px-2 py-0.5 rounded-full">내역 →</span>
                            </div>
                            <div className="text-5xl font-black text-white drop-shadow-[0_0_15px_rgba(234,179,8,0.3)]">
                                {royaltyLoading ? '...' : (royaltySummary?.total_earned ?? 0).toLocaleString()}
                            </div>
                            <div className="mt-4 text-xs font-mono text-white/40 bg-black/30 w-fit px-2 py-1 rounded border border-white/5">
                                {royaltySummary?.pending ?? 0} 지급 대기
                            </div>
                        </div>
                    </Link>

                    <div className="p-8 bg-black/40 backdrop-blur-xl border border-[#c1ff00]/20 rounded-3xl relative overflow-hidden group">
                        <div className="absolute inset-0 bg-[#c1ff00]/5 group-hover:bg-[#c1ff00]/10 transition-colors" />
                        <div className="absolute top-0 right-0 p-6 opacity-20 text-6xl grayscale group-hover:grayscale-0 transition-all transform group-hover:scale-110 duration-500">👁️</div>
                        <div className="relative z-10">
                            <div className="text-sm font-black text-[#c1ff00] uppercase tracking-widest mb-2">TOTAL VIEWS</div>
                            <div className="text-5xl font-black text-white drop-shadow-[0_0_15px_rgba(193,255,0,0.3)] italic">
                                {stats ? (stats.total_views / 10000).toFixed(1) : '0'}<span className="text-2xl text-white/50 ml-1 not-italic">M</span>
                            </div>
                            <div className="mt-4 text-xs font-mono text-white/60 bg-black/30 w-fit px-3 py-1.5 rounded-lg border border-white/5 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-[#c1ff00]" />
                                {stats?.node_count ?? 0} NODES ACTIVE
                            </div>
                        </div>
                    </div>

                    <div className="p-8 bg-black/40 backdrop-blur-xl border border-emerald-500/20 rounded-3xl relative overflow-hidden group">
                        <div className="absolute inset-0 bg-emerald-500/5 group-hover:bg-emerald-500/10 transition-colors" />
                        <div className="absolute top-0 right-0 p-6 opacity-20 text-6xl grayscale group-hover:grayscale-0 transition-all transform group-hover:scale-110 duration-500">🌿</div>
                        <div className="relative z-10">
                            <div className="text-sm font-bold text-emerald-300 uppercase tracking-widest mb-2">총 포크 수</div>
                            <div className="text-5xl font-black text-white drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                                {stats?.total_forks ?? 0}
                            </div>
                            <div className="mt-4 text-xs font-mono text-white/40 bg-black/30 w-fit px-2 py-1 rounded border border-white/5">
                                누적 포크 수
                            </div>
                        </div>
                    </div>

                    <div className="p-8 bg-black/40 backdrop-blur-xl border border-pink-500/20 rounded-3xl relative overflow-hidden group">
                        <div className="absolute inset-0 bg-pink-500/5 group-hover:bg-pink-500/10 transition-colors" />
                        <div className="absolute top-0 right-0 p-6 opacity-20 text-6xl grayscale group-hover:grayscale-0 transition-all transform group-hover:scale-110 duration-500">📈</div>
                        <div className="relative z-10">
                            <div className="text-sm font-bold text-pink-300 uppercase tracking-widest mb-2">평균 성과</div>
                            <div className="text-5xl font-black text-white drop-shadow-[0_0_15px_rgba(236,72,153,0.3)]">
                                +127%
                            </div>
                            <div className="mt-4 text-xs font-mono text-white/40 bg-black/30 w-fit px-2 py-1 rounded border border-white/5">
                                상위 5% 크리에이터
                            </div>
                        </div>
                    </div>
                </div>

                {/* Two Column Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                    {/* Viral Tree */}
                    <div>
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-2xl font-bold flex items-center gap-3">
                                <span className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center border border-white/10 text-lg">🌳</span>
                                계보 트리
                            </h2>
                        </div>

                        <div className="p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl min-h-[500px] relative overflow-hidden">
                            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.03] pointer-events-none" />
                            <div className="relative z-10">
                                {genealogyLoading ? (
                                    <div className="flex flex-col items-center justify-center h-[400px] text-white/30 gap-4">
                                        <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
                                        <div className="text-sm">계보를 추적하는 중...</div>
                                    </div>
                                ) : genealogyTree ? (
                                    <TreeNodeCard
                                        node={genealogyTree}
                                        onSelect={setSelectedNode}
                                        selectedId={selectedNode}
                                    />
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-[400px] text-white/30">
                                        <div className="text-4xl mb-4">🕸️</div>
                                        <div className="text-center">
                                            <p className="mb-2">선택된 노드의 계보 데이터가 없습니다</p>
                                            <p className="text-xs">오른쪽 목록에서 다른 리믹스를 선택해보세요</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {selectedNode && (
                            <div className="mt-4 p-6 bg-violet-600/10 border border-violet-500/20 rounded-2xl flex justify-between items-center animate-pulse-glow">
                                <div>
                                    <div className="text-xs text-violet-300 font-bold uppercase tracking-wider mb-1">선택된 노드</div>
                                    <div className="text-sm font-mono text-white/80">{selectedNode}</div>
                                </div>
                                <Link
                                    href={`/remix/${selectedNode}`}
                                    className="px-4 py-2 bg-violet-500 hover:bg-violet-400 text-white text-xs font-bold rounded-xl transition-colors shadow-[0_0_15px_rgba(139,92,246,0.3)]"
                                >
                                    상세 보기 →
                                </Link>
                            </div>
                        )}
                    </div>

                    {/* Recent Activity */}
                    <div>
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-2xl font-bold flex items-center gap-3">
                                <span className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center border border-white/10 text-lg">📊</span>
                                활동 피드
                            </h2>
                        </div>

                        <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                            {loading ? (
                                <div className="flex justify-center p-20">
                                    <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
                                </div>
                            ) : nodes.length === 0 ? (
                                <div className="p-16 text-center text-white/30 border border-dashed border-white/10 rounded-3xl bg-white/5">
                                    <div className="text-5xl mb-6 opacity-30">📭</div>
                                    <p className="font-bold text-lg mb-2">아직 활동 내역이 없습니다</p>
                                    <p className="text-sm mb-6 max-w-xs mx-auto">첫 번째 리믹스를 생성하여 바이럴 여정을 시작해보세요</p>
                                    <Link href="/canvas" className="inline-block px-6 py-3 bg-white text-black rounded-xl text-sm font-bold hover:shadow-[0_0_20px_rgba(255,255,255,0.3)] transition-all">
                                        첫 리믹스 만들기
                                    </Link>
                                </div>
                            ) : (
                                nodes.map((node) => (
                                    <div
                                        key={node.id}
                                        onClick={() => setSelectedNode(node.node_id)}
                                        className={`group cursor-pointer block p-5 backdrop-blur-md border rounded-2xl transition-all hover:translate-x-1 ${selectedNode === node.node_id
                                            ? 'bg-violet-500/10 border-violet-500/40'
                                            : 'bg-black/40 border-white/5 hover:border-white/20'
                                            }`}
                                    >
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <div className="font-bold text-lg text-white/90 group-hover:text-white transition-colors">{node.title}</div>
                                                <div className="flex items-center gap-3 mt-2">
                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${node.layer === 'master' ? 'bg-violet-500/10 text-violet-300 border-violet-500/20' :
                                                        node.layer === 'fork' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' :
                                                            'bg-pink-500/10 text-pink-300 border-pink-500/20'
                                                        }`}>
                                                        {node.layer}
                                                    </span>
                                                    <span className="text-xs text-white/40">
                                                        {new Date(node.created_at).toLocaleDateString()}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-sm font-bold text-white group-hover:scale-110 transition-transform origin-right">
                                                    {node.view_count.toLocaleString()} <span className="text-xs text-white/40 font-normal">조회</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Quick Actions */}
                {/* Recommended Remixes Flow */}
                <div className="mt-20">
                    <h3 className="text-sm font-black text-white/40 uppercase tracking-widest mb-6 border-b border-white/10 pb-4">Quick Actions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <Link
                            href="/canvas"
                            className="p-8 bg-black/40 border border-[#c1ff00]/20 hover:border-[#c1ff00]/50 rounded-2xl relative overflow-hidden group transition-all hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(193,255,0,0.1)]"
                        >
                            <div className="absolute inset-0 bg-[#c1ff00]/5 group-hover:bg-[#c1ff00]/10 transition-colors" />
                            <div className="text-4xl mb-6 group-hover:scale-110 transition-transform duration-300 filter drop-shadow-[0_0_10px_rgba(193,255,0,0.5)]">⚡</div>
                            <div className="font-black text-xl mb-1 text-white italic uppercase tracking-tighter">NEW ENGINE</div>
                            <div className="text-xs text-[#c1ff00] font-bold uppercase tracking-wider">Start Blank Canvas</div>
                        </Link>

                        <Link
                            href="/o2o"
                            className="p-8 bg-black/40 border border-white/10 hover:border-white/30 rounded-2xl relative overflow-hidden group transition-all hover:-translate-y-1"
                        >
                            <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                            <div className="text-4xl mb-6 group-hover:scale-110 transition-transform duration-300 grayscale group-hover:grayscale-0">🛒</div>
                            <div className="font-black text-xl mb-1 text-white italic uppercase tracking-tighter">O2O CAMPAIGN</div>
                            <div className="text-xs text-white/40 font-bold uppercase tracking-wider group-hover:text-white/60">Explore Campaigns</div>
                        </Link>

                        <Link
                            href="/"
                            className="p-8 bg-black/40 border border-white/10 hover:border-white/30 rounded-2xl relative overflow-hidden group transition-all hover:-translate-y-1"
                        >
                            <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                            <div className="text-4xl mb-6 group-hover:scale-110 transition-transform duration-300 grayscale group-hover:grayscale-0">🔁</div>
                            <div className="font-black text-xl mb-1 text-white italic uppercase tracking-tighter">FIND REMIX</div>
                            <div className="text-xs text-white/40 font-bold uppercase tracking-wider group-hover:text-white/60">Back to Outliers</div>
                        </Link>
                    </div>
                </div>

                {/* Account Section */}
                <div className="mt-16 pt-8 border-t border-white/10">
                    <h3 className="text-sm font-black text-white/40 uppercase tracking-widest mb-6">Account</h3>
                    <div className="flex items-center justify-between p-6 bg-black/40 border border-white/10 rounded-2xl group hover:border-white/30 transition-colors">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-lg bg-[#c1ff00] flex items-center justify-center text-black font-black text-xl shadow-[0_0_15px_rgba(193,255,0,0.3)]">
                                {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                            </div>
                            <div>
                                <div className="font-bold text-white uppercase tracking-wider">{user?.name || 'User'}</div>
                                <div className="text-sm text-white/40 font-mono">{user?.email}</div>
                            </div>
                        </div>
                        <button
                            onClick={() => {
                                logout();
                                router.push('/');
                            }}
                            className="px-6 py-2 text-xs font-bold uppercase tracking-widest text-[#c1ff00] border border-[#c1ff00]/30 hover:bg-[#c1ff00] hover:text-black rounded-lg transition-all shadow-[0_0_10px_rgba(193,255,0,0.1)] hover:shadow-[0_0_20px_rgba(193,255,0,0.4)]"
                        >
                            LOGOUT
                        </button>
                    </div>
                </div>
            </main>
        </div>
    );
}
