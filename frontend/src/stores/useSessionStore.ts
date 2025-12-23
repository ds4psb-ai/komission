// frontend/src/stores/useSessionStore.ts
// Zustand store for Session-based architecture with persist middleware

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
    RemixSession,
    Outlier,
    QuestRef,
    VariableSlot,
    SessionPhase,
    SessionTab,
    SessionMode,
    RecipeRef,
    RunRef,
} from "@/lib/types/session";

// ─────────────────────────────────────────────────────────────
// Action Types
// ─────────────────────────────────────────────────────────────

type SessionActions = {
    // Initialization
    initFromRoute: (input: {
        nodeId?: string;
        tab?: SessionTab;
        sessionId?: string;
    }) => void;

    // Mode & Tab
    setMode: (mode: SessionMode) => void;
    setTab: (tab: SessionTab) => void;

    // Outlier & Recipe
    setOutlier: (outlier: Outlier) => void;
    setRecipe: (recipe: RecipeRef) => void;

    // Variable Slots
    setSlots: (slots: VariableSlot[]) => void;
    patchSlot: (slotId: string, value: unknown) => void;

    // Quest
    acceptQuest: (quest: QuestRef) => void;
    clearQuest: () => void;

    // Phase & Run
    setPhase: (phase: SessionPhase) => void;
    setRunCreated: (run: { runId: string; forkNodeId?: string }) => void;
    setRunStatus: (status: RunRef["status"]) => void;

    // Reset
    resetSession: () => void;
};

// ─────────────────────────────────────────────────────────────
// Initial State Factory
// ─────────────────────────────────────────────────────────────

const newSession = (): RemixSession => ({
    sessionId: typeof crypto !== "undefined" ? crypto.randomUUID() : Date.now().toString(),
    phase: "discover",
    slots: [],
    mode: "simple",
    activeTab: "shoot",
    updatedAt: Date.now(),
});

// ─────────────────────────────────────────────────────────────
// Store Definition
// ─────────────────────────────────────────────────────────────

export const useSessionStore = create<RemixSession & SessionActions>()(
    persist(
        (set) => ({
            ...newSession(),

            // ─── Initialization ───────────────────────────────────
            initFromRoute: ({ nodeId, tab, sessionId }) =>
                set((s) => ({
                    ...s,
                    sessionId: sessionId ?? s.sessionId,
                    activeTab: tab ?? s.activeTab,
                    outlier: nodeId
                        ? { ...(s.outlier ?? ({} as Outlier)), nodeId }
                        : s.outlier,
                    updatedAt: Date.now(),
                })),

            // ─── Mode & Tab ───────────────────────────────────────
            setMode: (mode) => set({ mode, updatedAt: Date.now() }),
            setTab: (activeTab) => set({ activeTab, updatedAt: Date.now() }),

            // ─── Outlier & Recipe ─────────────────────────────────
            // Only advance phase to "setup" if currently in "discover", don't reset
            setOutlier: (outlier) =>
                set((s) => ({
                    outlier,
                    phase: s.phase === "discover" ? "setup" : s.phase,
                    updatedAt: Date.now(),
                })),
            setRecipe: (recipe) => set({ recipe, updatedAt: Date.now() }),

            // ─── Variable Slots ───────────────────────────────────
            setSlots: (slots) => set({ slots, updatedAt: Date.now() }),
            patchSlot: (slotId, value) =>
                set((s) => ({
                    slots: s.slots.map((x) =>
                        x.slotId === slotId ? { ...x, value } : x
                    ),
                    updatedAt: Date.now(),
                })),

            // ─── Quest ────────────────────────────────────────────
            acceptQuest: (quest) =>
                set({ quest: { ...quest, status: "accepted" }, updatedAt: Date.now() }),
            clearQuest: () => set({ quest: undefined, updatedAt: Date.now() }),

            // ─── Phase & Run ──────────────────────────────────────
            setPhase: (phase) => set({ phase, updatedAt: Date.now() }),
            setRunCreated: ({ runId, forkNodeId }) =>
                set({
                    run: {
                        runId,
                        forkNodeId,
                        status: "created",
                        startedAt: new Date().toISOString(),
                    },
                    phase: "shoot",
                    updatedAt: Date.now(),
                }),
            setRunStatus: (status) =>
                set((s) => ({
                    run: s.run ? { ...s.run, status } : s.run,
                    phase:
                        status === "submitted"
                            ? "submit"
                            : status === "tracking"
                                ? "track"
                                : s.phase,
                    updatedAt: Date.now(),
                })),

            // ─── Reset ────────────────────────────────────────────
            resetSession: () => set({ ...newSession() }),
        }),
        {
            name: "komission.session",
            storage: createJSONStorage(() => localStorage),
            partialize: (s) => ({
                sessionId: s.sessionId,
                phase: s.phase,
                outlier: s.outlier,
                recipe: s.recipe,
                slots: s.slots,
                quest: s.quest,
                run: s.run,
                mode: s.mode,
                activeTab: s.activeTab,
                updatedAt: s.updatedAt,
            }),
        }
    )
);

// ─────────────────────────────────────────────────────────────
// Selector Hooks (for optimized re-renders)
// ─────────────────────────────────────────────────────────────

export const useSessionPhase = () => useSessionStore((s) => s.phase);
export const useSessionMode = () => useSessionStore((s) => s.mode);
export const useSessionTab = () => useSessionStore((s) => s.activeTab);
export const useSessionOutlier = () => useSessionStore((s) => s.outlier);
export const useSessionQuest = () => useSessionStore((s) => s.quest);
export const useSessionRun = () => useSessionStore((s) => s.run);
