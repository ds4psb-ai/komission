// frontend/src/app/remix/[nodeId]/layout.tsx
// RSC Layout with RemixShell wrapper

import { RemixShell } from "@/components/remix/RemixShell";
import { getRemixSummary } from "./_lib/getRemixSummary";

interface RemixLayoutProps {
    children: React.ReactNode;
    params: Promise<{ nodeId: string }>;
}

export default async function RemixLayout({ children, params }: RemixLayoutProps) {
    const { nodeId } = await params;
    const nodeSummary = await getRemixSummary(nodeId);

    return (
        <RemixShell nodeId={nodeId} nodeSummary={nodeSummary}>
            {children}
        </RemixShell>
    );
}
