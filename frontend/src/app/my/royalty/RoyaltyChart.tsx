"use client";

import React, { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { RoyaltyTransaction } from '@/lib/api';

interface RoyaltyChartProps {
    transactions: RoyaltyTransaction[];
}

export function RoyaltyChart({ transactions }: RoyaltyChartProps) {
    const data = useMemo(() => {
        // Group by Date (YYYY-MM-DD)
        const grouped = transactions.reduce((acc, tx) => {
            const date = new Date(tx.created_at).toLocaleDateString();
            acc[date] = (acc[date] || 0) + tx.points_earned;
            return acc;
        }, {} as Record<string, number>);

        // Sort by date and convert to array
        return Object.entries(grouped)
            .map(([date, points]) => ({ date, points }))
            .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
            .slice(-30); // Last 30 days usually
    }, [transactions]);

    if (data.length === 0) return null;

    return (
        <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="colorPoints" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                    <XAxis
                        dataKey="date"
                        stroke="#ffffff40"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(value) => value.split('.').slice(1).join('/')}
                    />
                    <YAxis stroke="#ffffff40" tick={{ fontSize: 10 }} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#000000bb', borderColor: '#ffffff20', borderRadius: '12px' }}
                        itemStyle={{ color: '#fff' }}
                    />
                    <Area
                        type="monotone"
                        dataKey="points"
                        stroke="#8b5cf6"
                        fillOpacity={1}
                        fill="url(#colorPoints)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
