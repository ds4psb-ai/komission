// frontend/src/app/remix/[nodeId]/_lib/getRemixSummary.ts
// RSC-first data fetching with cache tags

export interface RemixSummary {
    node_id: string;
    title: string;
    platform?: string;
    layer?: string;
    view_count?: number;
    source_video_url?: string;
    thumbnail_url?: string;
    performance_delta?: string;
    genealogy_depth?: number;
    created_at?: string;
}

export async function getRemixSummary(nodeId: string): Promise<RemixSummary | null> {
    try {
        const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

        const res = await fetch(`${apiUrl}/api/v1/remix/${nodeId}`, {
            next: {
                tags: [`remix:${nodeId}`],
                revalidate: 60, // Revalidate every 60 seconds
            },
        });

        if (!res.ok) {
            console.warn(`[getRemixSummary] Failed to fetch node ${nodeId}: ${res.status}`);
            return null;
        }

        return res.json();
    } catch (error) {
        console.error(`[getRemixSummary] Error fetching node ${nodeId}:`, error);
        return null;
    }
}
