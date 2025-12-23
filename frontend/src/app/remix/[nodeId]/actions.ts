// frontend/src/app/remix/[nodeId]/actions.ts
"use server";

import { revalidatePath } from "next/cache";

// NOTE: Server Actions cannot access localStorage tokens.
// For authenticated endpoints, use client-side api.ts instead.
// These actions are kept for non-authenticated operations or future cookie-based auth.

const API_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to safely revalidate path
async function safeRevalidate(nodeId: string) {
    try {
        revalidatePath(`/remix/${nodeId}`);
        revalidatePath(`/remix/${nodeId}/shoot`);
        revalidatePath(`/remix/${nodeId}/earn`);
    } catch (e) {
        console.warn("[safeRevalidate] Failed:", e);
    }
}

/**
 * Server Action: Analyze a remix node
 * @deprecated Use api.analyzeNode() from client for authenticated requests
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

        await safeRevalidate(nodeId);
        return { success: true };
    } catch (error) {
        console.error("[analyzeNodeAction] Error:", error);
        return { success: false, error: String(error) };
    }
}

/**
 * Server Action: Fork a remix node (create mutation)
 * @deprecated Use api.forkRemixNode() from client for authenticated requests
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
 * NOTE: Quest API route does not exist yet in backend.
 * TODO: Implement /api/v1/o2o/campaigns/{id}/accept when ready
 * @deprecated Use client-side store.acceptQuest() for now
 */
export async function acceptQuestAction(_nodeId: string, _questId: string) {
    // Quest accept is handled client-side via useSessionStore.acceptQuest()
    // This action is a placeholder for future backend integration
    console.warn("[acceptQuestAction] Quest API not implemented yet. Using client-side store.");
    return { success: true };
}


