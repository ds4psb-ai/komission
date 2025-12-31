// frontend/src/components/remix/RemixShell.tsx
"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { SessionHUD } from "./SessionHUD";
import { RemixTabsNav } from "./RemixTabsNav";
import { useSessionStore } from "@/stores/useSessionStore";
import { SESSION_TABS, type SessionTab } from "@/lib/types/session";

interface NodeSummary {
    node_id: string;
    title: string;
    platform?: string;
    layer?: string;
    view_count?: number;
    source_video_url?: string;
    performance_delta?: string;
}

interface RemixShellProps {
    children: React.ReactNode;
    nodeId: string;
    nodeSummary: NodeSummary | null;
}

export function RemixShell({ children, nodeId, nodeSummary }: RemixShellProps) {
    const initFromRoute = useSessionStore((s) => s.initFromRoute);
    const setOutlier = useSessionStore((s) => s.setOutlier);
    const searchParams = useSearchParams();
    const tabParam = searchParams.get("tab");
    const routeTab = SESSION_TABS.find((entry) => entry.tab === tabParam)?.tab as SessionTab | undefined;

    // Initialize session from route
    useEffect(() => {
        initFromRoute({ nodeId, tab: routeTab });

        // Set outlier if we have node summary
        if (nodeSummary) {
            const parsedGrowthRate = nodeSummary.performance_delta
                ? parseFloat(nodeSummary.performance_delta.replace(/[^0-9.-]/g, ""))
                : NaN;
            setOutlier({
                nodeId: nodeSummary.node_id,
                title: nodeSummary.title,
                sourceUrl: nodeSummary.source_video_url || "",
                platform: nodeSummary.platform as any,
                growthRatePct: Number.isFinite(parsedGrowthRate) ? parsedGrowthRate : undefined,
            });
        }
    }, [nodeId, nodeSummary, routeTab, initFromRoute, setOutlier]);

    return (
        <div className="min-h-screen bg-black text-white">
            <AppHeader />
            <SessionHUD nodeId={nodeId} />
            <RemixTabsNav nodeId={nodeId} />
            <main className="container mx-auto px-6 py-8">
                {children}
            </main>
        </div>
    );
}
