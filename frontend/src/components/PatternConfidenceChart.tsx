import React, { useEffect, useState, useRef } from 'react';
import { api, PatternRankingResponse } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export function PatternConfidenceChart() {
    const [rankingData, setRankingData] = useState<PatternRankingResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const isMountedRef = useRef(true);

    useEffect(() => {
        const fetchRanking = async () => {
            try {
                const res = await api.getPatternConfidenceRanking(3); // Min samples = 3
                if (!isMountedRef.current) return;
                setRankingData(res);
            } catch (err) {
                console.error("Failed to fetch pattern ranking:", err);
            } finally {
                if (isMountedRef.current) {
                    setLoading(false);
                }
            }
        };

        fetchRanking();
    }, []);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    if (loading) return <div className="glass-panel p-6 rounded-2xl animate-pulse h-64"></div>;
    if (!rankingData || rankingData.ranking.length === 0) return null;

    // Transform data for Recharts
    const chartData = rankingData.ranking.map(item => ({
        name: item.pattern_code.replace(/^(VIS|AUD)_/, ''), // Shorten name
        confidence: Math.round(item.confidence * 100),
        type: item.pattern_type
    }));

    return (
        <div className="glass-panel p-6 rounded-2xl h-80">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-bold text-white/40 uppercase tracking-widest">
                    패턴 신뢰도 랭킹 (Top Patterns)
                </h3>
                <span className="text-xs text-white/30">
                    검증된 패턴: {rankingData.total_patterns}개
                </span>
            </div>

            <ResponsiveContainer width="100%" height="90%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                    <XAxis type="number" domain={[0, 100]} hide />
                    <YAxis
                        type="category"
                        dataKey="name"
                        tick={{ fill: '#94a3b8', fontSize: 10 }}
                        width={100}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                        formatter={(value: number | undefined) => [`${value ?? 0}%`, '신뢰도']}
                    />
                    <Bar dataKey="confidence" radius={[0, 4, 4, 0]} barSize={20}>
                        {chartData.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={entry.type === 'visual' ? '#8b5cf6' : '#10b981'} // Violet for Visual, Emerald for Audio
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
