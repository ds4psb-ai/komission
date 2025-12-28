// frontend/src/lib/types/session.ts
// Domain types for Session-based architecture
// Phase: discover → setup → shoot → submit → track

export type Id = string;

// ─────────────────────────────────────────────────────────────
// Core Entity Types
// ─────────────────────────────────────────────────────────────

export interface Outlier {
    nodeId: Id;
    title: string;
    sourceUrl: string;
    thumbnailUrl?: string;
    platform?: "tiktok" | "instagram" | "youtube" | "other";
    growthRatePct?: number;
    createdAt?: string;
    vdg_analysis?: {
        title?: string;
        title_ko?: string;
        total_duration?: number;
        scene_count?: number;
        scenes?: unknown[];
        hook_genome?: {
            pattern?: string;
            strength?: number;
            hook_summary?: string;
        };
        intent_layer?: unknown;
        capsule_brief?: unknown;
    };
}

export interface RecipeRef {
    recipeId: Id;       // pipeline/template id
    versionId?: Id;
    label?: string;
}

export interface VariableSlot {
    slotId: Id;
    label: string;
    kind: "text" | "choice" | "number" | "toggle";
    value: unknown;
    required?: boolean;
}

export interface QuestRef {
    campaignId: Id;
    title: string;
    rewardPoints: number;
    status: "suggested" | "accepted" | "applied" | "completed";
    campaignType?: "instant" | "onsite" | "shipment";
    placeName?: string;
    address?: string;
    deadline?: string;
    rewardProduct?: string | null;
}

export interface RunRef {
    runId: Id;
    forkNodeId?: Id;
    status: "idle" | "created" | "shooting" | "submitted" | "tracking";
    startedAt?: string;
}

// ─────────────────────────────────────────────────────────────
// Session Types
// ─────────────────────────────────────────────────────────────

export type SessionPhase = "discover" | "setup" | "shoot" | "submit" | "track";

export type SessionTab = "shoot" | "earn" | "analyze" | "genealogy" | "studio";

export type SessionMode = "simple" | "pro";

export interface RemixSession {
    sessionId: Id;
    phase: SessionPhase;
    outlier?: Outlier;
    recipe?: RecipeRef;
    slots: VariableSlot[];
    quest?: QuestRef;
    run?: RunRef;
    mode: SessionMode;
    activeTab: SessionTab;
    updatedAt: number;
}

// ─────────────────────────────────────────────────────────────
// Helper Types for Components
// ─────────────────────────────────────────────────────────────

export interface SessionPhaseInfo {
    phase: SessionPhase;
    label: string;
    description: string;
    icon: string;
}

export const SESSION_PHASES: SessionPhaseInfo[] = [
    { phase: "discover", label: "발견", description: "아웃라이어 선택", icon: "🔍" },
    { phase: "setup", label: "설정", description: "레시피 커스터마이징", icon: "⚙️" },
    { phase: "shoot", label: "촬영", description: "콘텐츠 제작", icon: "🎬" },
    { phase: "submit", label: "제출", description: "완성 및 업로드", icon: "📤" },
    { phase: "track", label: "추적", description: "성과 모니터링", icon: "📊" },
];

export const SESSION_TABS: { tab: SessionTab; label: string; icon: string; proOnly?: boolean }[] = [
    { tab: "shoot", label: "촬영", icon: "🎬" },
    { tab: "earn", label: "수익", icon: "💰" },
    { tab: "analyze", label: "분석", icon: "🧬", proOnly: true },
    { tab: "genealogy", label: "계보", icon: "🌳", proOnly: true },
    { tab: "studio", label: "스튜디오", icon: "🎛️", proOnly: true },
];
