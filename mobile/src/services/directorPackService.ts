/**
 * DirectorPack Service - Phase 1.1
 * 
 * Ported from frontend: session/shoot/page.tsx
 * 
 * Features:
 * - DirectorPack API loading
 * - Checkpoint-based guide extraction
 * - Fallback handling
 * - Offline support
 */

// ============================================================
// Types (ported from frontend)
// ============================================================

export interface Checkpoint {
    checkpoint_id: string;
    t_window: [number, number];
    active_rules: string[];
    note?: string;
}

export interface DNAInvariant {
    rule_id: string;
    domain: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    check_hint?: string;
    coach_line_templates?: {
        strict?: string;
        friendly?: string;
        neutral?: string;
    };
}

export interface DirectorPack {
    pack_version: string;
    pattern_id: string;
    goal?: string;
    target?: {
        duration_target_sec?: number;
        platform?: string;
    };
    dna_invariants: DNAInvariant[];
    checkpoints: Checkpoint[];
    mutation_slots?: Array<{
        slot_id: string;
        slot_type: string;
        guide?: string;
    }>;
    policy?: {
        cooldown_sec?: number;
    };
}

export interface GuideStep {
    time: string;
    timeWindow: [number, number];  // [start_sec, end_sec] for tracking
    action: string;
    icon: string;
    priority?: 'critical' | 'high' | 'medium' | 'low';
    ruleId?: string;
    reason?: string;
}

export interface GuideData {
    title: string;
    bpm: number;
    duration: number;
    steps: GuideStep[];
    tips: string[];
    goal?: string;
    isLive: boolean;
    analyzedCount?: number;
}

// ============================================================
// Constants
// ============================================================

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const API_TIMEOUT_MS = 10000;

const PRIORITY_ICONS: Record<string, string> = {
    critical: '🔴',
    high: '🟠',
    medium: '🟡',
    low: '🟢',
};

const DOMAIN_ICONS: Record<string, string> = {
    composition: '🎬',
    timing: '⏱️',
    audio: '🎵',
    performance: '🎭',
    text: '💬',
    safety: '⚠️',
    hook: '💥',
    pacing: '🎵',
    visual: '👁️',
    narrative: '📖',
    cta: '👆',
};

// ============================================================
// Fallback Guide
// ============================================================

export const FALLBACK_GUIDE: GuideData = {
    title: '2초 텍스트 펀치로 시작하는 숏폼',
    bpm: 120,
    duration: 15,
    steps: [
        {
            time: '0-2초',
            timeWindow: [0, 2],
            action: '텍스트 펀치로 시선 고정',
            icon: '💥',
            priority: 'critical',
            reason: '첫 2초 이탈률을 47% 낮춰요',
        },
        {
            time: '2-5초',
            timeWindow: [2, 5],
            action: '제품 클로즈업',
            icon: '📦',
            priority: 'high',
        },
        {
            time: '5-10초',
            timeWindow: [5, 10],
            action: '사용 장면 시연',
            icon: '✨',
            priority: 'medium',
        },
        {
            time: '10-15초',
            timeWindow: [10, 15],
            action: 'CTA + 아웃트로',
            icon: '👆',
            priority: 'medium',
        },
    ],
    tips: [
        '첫 2초가 가장 중요! 화면을 멈추게 하세요',
        '배경 음악은 K-POP 트렌딩 추천',
        '자연광이 가장 좋아요',
    ],
    isLive: false,
};

// ============================================================
// Helper Functions
// ============================================================

function formatTimeWindow(tw: [number, number], totalDuration: number): string {
    const startSec = Math.round(tw[0] * totalDuration);
    const endSec = Math.round(tw[1] * totalDuration);
    return `${startSec}-${endSec}초`;
}

function getTimeWindowSeconds(tw: [number, number], totalDuration: number): [number, number] {
    return [
        Math.round(tw[0] * totalDuration),
        Math.round(tw[1] * totalDuration),
    ];
}

function generateReason(rule: DNAInvariant): string {
    const priorityReasons: Record<string, string> = {
        critical: '이 패턴에서 가장 중요한 요소예요',
        high: '성공한 영상의 85%가 이 요소를 포함해요',
        medium: '이 패턴의 핵심 시그니처예요',
        low: '추가하면 더 좋은 결과가 나와요',
    };

    const domainReasons: Record<string, string> = {
        hook: '첫 2초 이탈률을 47% 낮춰요',
        pacing: '시청 완료율과 직결돼요',
        audio: '음악 싱크가 맞으면 공유율 2배',
        visual: '시선 유지에 효과적이에요',
        narrative: '스토리 전달력을 높여요',
        cta: '댓글/좋아요를 유도해요',
    };

    return domainReasons[rule.domain] || priorityReasons[rule.priority] || '';
}

// ============================================================
// Main Functions
// ============================================================

/**
 * Extract guide from DirectorPack
 * Ported from frontend: extractGuideFromDirectorPack()
 */
export function extractGuideFromDirectorPack(
    pack: DirectorPack,
    patternSummary?: string
): GuideData {
    const duration = pack.target?.duration_target_sec || 15;

    // Convert checkpoints + DNA invariants to steps
    const steps: GuideStep[] = [];

    // Create rule lookup
    const ruleMap = new Map<string, DNAInvariant>();
    pack.dna_invariants.forEach(inv => ruleMap.set(inv.rule_id, inv));

    // Process checkpoints
    pack.checkpoints.forEach(cp => {
        cp.active_rules.forEach(ruleId => {
            const rule = ruleMap.get(ruleId);
            if (rule) {
                const action = rule.coach_line_templates?.friendly
                    || rule.coach_line_templates?.neutral
                    || rule.check_hint
                    || ruleId;

                const reason = generateReason(rule);
                const timeWindow = getTimeWindowSeconds(cp.t_window, duration);

                steps.push({
                    time: formatTimeWindow(cp.t_window, duration),
                    timeWindow,
                    action,
                    icon: DOMAIN_ICONS[rule.domain] || PRIORITY_ICONS[rule.priority] || '📌',
                    priority: rule.priority,
                    ruleId: rule.rule_id,
                    reason,
                });
            }
        });
    });

    // If no checkpoints, use DNA invariants directly
    if (steps.length === 0) {
        pack.dna_invariants.slice(0, 5).forEach((inv, i) => {
            const action = inv.coach_line_templates?.friendly
                || inv.check_hint
                || inv.rule_id;

            steps.push({
                time: '전체',
                timeWindow: [0, duration],
                action,
                icon: DOMAIN_ICONS[inv.domain] || '📌',
                priority: inv.priority,
                ruleId: inv.rule_id,
            });
        });
    }

    // Generate tips from mutation slots
    const tips: string[] = [];
    pack.mutation_slots?.slice(0, 3).forEach(slot => {
        if (slot.guide) {
            tips.push(slot.guide);
        }
    });

    // Add generic tips if not enough
    if (tips.length < 2) {
        tips.push('첫 2초가 가장 중요! 화면을 멈추게 하세요');
        tips.push('자연광이 가장 좋아요');
    }

    return {
        title: pack.goal || patternSummary || `${pack.pattern_id} 패턴`,
        bpm: 120,
        duration,
        steps,
        tips,
        goal: pack.goal,
        isLive: true,
    };
}

/**
 * Load DirectorPack from API
 */
export async function loadDirectorPack(patternId: string): Promise<{
    pack: DirectorPack | null;
    guide: GuideData;
    error: string | null;
}> {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

        const response = await fetch(
            `${API_BASE_URL}/outliers/items/${patternId}`,
            {
                headers: { 'Accept': 'application/json' },
                signal: controller.signal,
            }
        );

        clearTimeout(timeoutId);

        if (!response.ok) {
            if (response.status === 404) {
                console.warn('[DirectorPack] Pattern not found, using fallback');
                return { pack: null, guide: FALLBACK_GUIDE, error: null };
            }
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        // Check if DirectorPack is available
        if (data.director_pack) {
            const pack = data.director_pack as DirectorPack;
            const guide = extractGuideFromDirectorPack(pack, data.title);
            console.log('[DirectorPack] Loaded:', pack.pattern_id);
            return { pack, guide, error: null };
        }

        // Fallback: use analysis checkpoints
        if (data.analysis?.checkpoints) {
            const steps = data.analysis.checkpoints.map((cp: Checkpoint, i: number) => ({
                time: `${cp.t_window[0]}-${cp.t_window[1]}초`,
                timeWindow: cp.t_window,
                action: cp.note || `체크포인트 ${i + 1}`,
                icon: '📍',
            }));

            const guide: GuideData = {
                title: data.title || FALLBACK_GUIDE.title,
                bpm: 120,
                duration: data.analysis?.hook_duration_sec || 15,
                steps: steps.length > 0 ? steps : FALLBACK_GUIDE.steps,
                tips: FALLBACK_GUIDE.tips,
                isLive: steps.length > 0,
            };

            console.log('[DirectorPack] Using analysis checkpoints');
            return { pack: null, guide, error: null };
        }

        // Fallback: use viral kicks
        if (data.shooting_guide?.kicks) {
            interface ViralKick {
                t_start_ms: number;
                t_end_ms: number;
                creator_instruction?: string;
                title?: string;
            }

            const steps = data.shooting_guide.kicks.slice(0, 5).map((kick: ViralKick) => ({
                time: `${Math.round(kick.t_start_ms / 1000)}-${Math.round(kick.t_end_ms / 1000)}초`,
                timeWindow: [kick.t_start_ms / 1000, kick.t_end_ms / 1000] as [number, number],
                action: kick.creator_instruction || kick.title || '',
                icon: '🎬',
            }));

            const guide: GuideData = {
                title: data.title || FALLBACK_GUIDE.title,
                bpm: 120,
                duration: 15,
                steps,
                tips: FALLBACK_GUIDE.tips,
                isLive: true,
            };

            console.log('[DirectorPack] Using viral kicks');
            return { pack: null, guide, error: null };
        }

        // No coaching data available
        console.log('[DirectorPack] No data, using fallback');
        return {
            pack: null,
            guide: { ...FALLBACK_GUIDE, title: data.title || FALLBACK_GUIDE.title },
            error: null,
        };

    } catch (error) {
        let errorMessage = '가이드 로딩 실패';

        if (error instanceof Error) {
            if (error.name === 'AbortError') {
                errorMessage = '서버 응답 시간 초과';
            } else if (error.message.includes('fetch')) {
                errorMessage = '서버에 연결할 수 없습니다';
            } else {
                errorMessage = error.message;
            }
        }

        console.error('[DirectorPack] Error:', errorMessage);
        return { pack: null, guide: FALLBACK_GUIDE, error: errorMessage };
    }
}

/**
 * Get current step based on recording time
 */
export function getCurrentStep(
    guide: GuideData,
    currentTimeSec: number
): GuideStep | null {
    return guide.steps.find(step =>
        currentTimeSec >= step.timeWindow[0] &&
        currentTimeSec < step.timeWindow[1]
    ) || null;
}

/**
 * Get upcoming step (for pre-alert)
 */
export function getUpcomingStep(
    guide: GuideData,
    currentTimeSec: number,
    preAlertSec: number = 2
): GuideStep | null {
    return guide.steps.find(step =>
        step.timeWindow[0] > currentTimeSec &&
        step.timeWindow[0] - currentTimeSec <= preAlertSec
    ) || null;
}

/**
 * Sort steps by priority
 */
export function sortStepsByPriority(steps: GuideStep[]): GuideStep[] {
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    return [...steps].sort((a, b) => {
        const aPriority = a.priority ? priorityOrder[a.priority] : 4;
        const bPriority = b.priority ? priorityOrder[b.priority] : 4;
        return aPriority - bPriority;
    });
}

export default {
    loadDirectorPack,
    extractGuideFromDirectorPack,
    getCurrentStep,
    getUpcomingStep,
    sortStepsByPriority,
    FALLBACK_GUIDE,
};
