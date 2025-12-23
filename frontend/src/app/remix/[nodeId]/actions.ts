// frontend/src/app/remix/[nodeId]/actions.ts
"use server";

import { revalidatePath } from "next/cache";

const API_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to safely revalidate path
async function safeRevalidate(nodeId: string) {
    try {
        revalidatePath(`/remix/${nodeId}`);
    } catch (e) {
        console.warn("[safeRevalidate] Failed:", e);
    }
}

/**
 * Server Action: Analyze a remix node
 */
export async function analyzeNodeAction(nodeId: string) {
    try {
        const res = await fetch(`${API_URL}/api/v1/remix/${nodeId}/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        if (!res.ok) {
            throw new Error(`Analysis failed: ${res.status}`);
        }

        // Invalidate cache for this node
        await safeRevalidate(nodeId);

        return { success: true };
    } catch (error) {
        console.error("[analyzeNodeAction] Error:", error);
        return { success: false, error: String(error) };
    }
}

/**
 * Server Action: Fork a remix node (create mutation)
 */
export async function forkNodeAction(nodeId: string) {
    try {
        const res = await fetch(`${API_URL}/api/v1/remix/${nodeId}/fork`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        if (!res.ok) {
            throw new Error(`Fork failed: ${res.status}`);
        }

        const data = await res.json();
        await safeRevalidate(nodeId);

        return { success: true, forkedNodeId: data.node_id };
    } catch (error) {
        console.error("[forkNodeAction] Error:", error);
        return { success: false, error: String(error) };
    }
}

/**
 * Server Action: Accept a quest for current session
 */
export async function acceptQuestAction(nodeId: string, questId: string) {
    try {
        const res = await fetch(`${API_URL}/api/v1/quest/${questId}/accept`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ node_id: nodeId }),
        });

        if (!res.ok) {
            throw new Error(`Quest accept failed: ${res.status}`);
        }

        return { success: true };
    } catch (error) {
        console.error("[acceptQuestAction] Error:", error);
        return { success: false, error: String(error) };
    }
}

