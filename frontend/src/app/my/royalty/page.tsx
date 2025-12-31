"use client";

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AppHeader } from '@/components/AppHeader';
import { api, RoyaltySummary, RoyaltyTransaction } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { RoyaltyChart } from './RoyaltyChart';

export default function RoyaltyHistoryPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading: authLoading } = useAuth();

    const [summary, setSummary] = useState<RoyaltySummary | null>(null);
    const [history, setHistory] = useState<RoyaltyTransaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');
    const isMountedRef = useRef(true);

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push('/login?redirect=/my/royalty');
            return;
        }

        if (isAuthenticated) {
            loadData();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [authLoading, isAuthenticated, filter]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    async function loadData() {
        if (isMountedRef.current) {
            setLoading(true);
        }
        try {
            const [summaryData, historyData] = await Promise.all([
                api.getMyRoyalty(),
                api.getRoyaltyHistory(filter === 'all' ? undefined : filter)
            ]);
            if (!isMountedRef.current) return;
            setSummary(summaryData);
            setHistory(historyData);
        } catch (e) {
            console.error(e);
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    }

    const filters = [
        { id: 'all', label: 'All Transactions' },
        { id: 'fork', label: 'Fork Bonus' },
        { id: 'view_milestone', label: 'View Milestones' },
        { id: 'k_success', label: 'K-Success' }
    ];

    return (
        <div className="min-h-screen bg-black text-white selection:bg-yellow-500/30">
            <AppHeader />

            <main className="max-w-6xl mx-auto px-6 py-20">
                <div className="flex items-center gap-4 mb-2">
                    <Link href="/my" className="text-white/40 hover:text-white transition-colors">← Back to Dashboard</Link>
                </div>

                <h1 className="text-4xl font-black mb-8">
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-500">
                        Earnings History
                    </span>
                </h1>

                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                    <div className="p-6 bg-yellow-500/10 border border-yellow-500/20 rounded-2xl">
                        <div className="text-xs font-bold text-yellow-500 uppercase tracking-widest mb-1">Total Earned</div>
                        <div className="text-3xl font-black text-white">{summary?.total_earned.toLocaleString() ?? 0} <span className="text-sm font-normal text-white/50">pts</span></div>
                    </div>

                    <div className="p-6 bg-white/5 border border-white/10 rounded-2xl">
                        <div className="text-xs font-bold text-white/40 uppercase tracking-widest mb-1">Pending Settlement</div>
                        <div className="text-3xl font-black text-white">{summary?.pending.toLocaleString() ?? 0} <span className="text-sm font-normal text-white/50">pts</span></div>
                        <div className="text-[10px] text-white/30 mt-2">* Released after verification threshold</div>
                    </div>

                    <div className="p-6 bg-violet-500/10 border border-violet-500/20 rounded-2xl">
                        <div className="text-xs font-bold text-violet-400 uppercase tracking-widest mb-1">Current K-Points</div>
                        <div className="text-3xl font-black text-white">{summary?.k_points.toLocaleString() ?? 0} <span className="text-sm font-normal text-white/50">KP</span></div>
                    </div>
                </div>

                {/* Chart Section */}
                <div className="mb-8 p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl">
                    <h3 className="text-sm font-bold text-white/40 uppercase tracking-widest mb-6">Earnings Trend</h3>
                    <RoyaltyChart transactions={history} />
                </div>

                {/* Filters */}
                <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                    {filters.map(f => (
                        <button
                            key={f.id}
                            onClick={() => setFilter(f.id)}
                            className={`px-4 py-2 rounded-full text-sm font-bold whitespace-nowrap transition-all ${filter === f.id ? 'bg-white text-black' : 'bg-white/5 text-white/60 hover:bg-white/10'}`}
                        >
                            {f.label}
                        </button>
                    ))}
                </div>

                {/* History Table */}
                <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden">
                    {loading ? (
                        <div className="p-20 flex justify-center">
                            <div className="w-10 h-10 border-4 border-yellow-500 border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : history.length === 0 ? (
                        <div className="p-20 text-center text-white/30">
                            <div className="text-4xl mb-4">📜</div>
                            No transaction history found.
                        </div>
                    ) : (
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-white/10 text-white/40 text-xs font-bold uppercase tracking-wider">
                                    <th className="p-6">Date</th>
                                    <th className="p-6">Event Type</th>
                                    <th className="p-6">Source Node</th>
                                    <th className="p-6 text-right">Amount</th>
                                    <th className="p-6 text-right">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {history.map((tx) => {
                                    const createdAt = new Date(tx.created_at);
                                    const isValidDate = !Number.isNaN(createdAt.getTime());
                                    const dateLabel = isValidDate ? createdAt.toLocaleDateString() : '-';
                                    const timeLabel = isValidDate ? createdAt.toLocaleTimeString() : '-';
                                    return (
                                    <tr key={tx.id} className="hover:bg-white/5 transition-colors group">
                                        <td className="p-6 text-sm text-white/60 font-mono">
                                            {dateLabel}
                                            <div className="text-xs text-white/20">{timeLabel}</div>
                                        </td>
                                        <td className="p-6">
                                            <span className={`inline-flex items-center gap-2 px-2 py-1 rounded text-xs font-bold uppercase ${tx.reason === 'fork' ? 'bg-emerald-500/20 text-emerald-400' : tx.reason === 'view_milestone' ? 'bg-blue-500/20 text-blue-400' : tx.reason === 'k_success' ? 'bg-purple-500/20 text-purple-400' : 'bg-white/10 text-white/60'}`}>
                                                {tx.reason.replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td className="p-6 text-sm">
                                            <Link href={`/remix/${tx.source_node_id}`} className="hover:text-yellow-400 transition-colors">
                                                Node: <span className="font-mono text-white/60">{tx.source_node_id.substring(0, 12)}...</span>
                                            </Link>
                                            {tx.forked_node_id && (
                                                <div className="text-xs text-emerald-500/60 mt-1">
                                                    ↳ Forked: {tx.forked_node_id.substring(0, 8)}...
                                                </div>
                                            )}
                                        </td>
                                        <td className="p-6 text-right font-mono font-bold text-yellow-400 text-lg">
                                            +{tx.points_earned}
                                        </td>
                                        <td className="p-6 text-right">
                                            {tx.is_settled ? (
                                                <span className="text-xs text-green-500 font-bold">SETTLED</span>
                                            ) : (
                                                <span className="text-xs text-white/30 font-bold px-2 py-1 rounded border border-white/10">PENDING</span>
                                            )}
                                        </td>
                                    </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </main>
        </div>
    );
}
