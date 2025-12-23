// frontend/src/app/remix/[nodeId]/page.tsx
// Redirect to default tab (shoot)

import { redirect } from "next/navigation";

interface PageProps {
    params: Promise<{ nodeId: string }>;
}

export default async function RemixPage({ params }: PageProps) {
    const { nodeId } = await params;
    redirect(`/remix/${nodeId}/shoot`);
}
