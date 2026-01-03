import { useTranslations } from 'next-intl';
import { ReactNode, memo } from 'react';
import { cn } from '@/lib/utils';
import { Lock, Target } from 'lucide-react';

// ============================================================
// Types
// ============================================================

type NodeStatus = 'idle' | 'running' | 'done' | 'error';
type ColorTheme = 'emerald' | 'violet' | 'pink' | 'amber' | 'cyan';

interface NodeWrapperProps {
    children: ReactNode;
    title: string;
    colorClass: string; // e.g., "border-cyan-500/40"
    status?: NodeStatus;
    isLocked?: boolean;
    isVariableSlot?: boolean;
    viralBadge?: string;
    icon?: ReactNode;
    errorMessage?: string;
    className?: string;
}

// ============================================================
// Color Theme Mapping (replaces nested ternaries)
// ============================================================

const THEME_GRADIENTS: Record<ColorTheme, string> = {
    emerald: 'from-emerald-950/60 to-emerald-900/20',
    violet: 'from-violet-950/60 to-violet-900/20',
    pink: 'from-rose-950/60 to-rose-900/20',
    amber: 'from-amber-950/60 to-amber-900/20',
    cyan: 'from-cyan-950/60 to-cyan-900/20',
};

const THEME_GLOWS: Record<ColorTheme, string> = {
    emerald: 'from-emerald-500',
    violet: 'from-violet-500',
    pink: 'from-rose-500',
    amber: 'from-amber-500',
    cyan: 'from-cyan-500',
};

/**
 * Detects color theme from colorClass string
 */
function detectTheme(colorClass: string): ColorTheme {
    if (colorClass.includes('emerald') || colorClass.includes('green')) return 'emerald';
    if (colorClass.includes('violet') || colorClass.includes('purple')) return 'violet';
    if (colorClass.includes('pink') || colorClass.includes('rose')) return 'pink';
    if (colorClass.includes('amber') || colorClass.includes('orange')) return 'amber';
    return 'cyan'; // default
}

// ============================================================
// Status Indicator Component (extracted for clarity)
// ============================================================

const StatusIndicator = memo(({ status }: { status?: NodeStatus }) => {
    switch (status) {
        case 'running':
            return (
                <div className="relative w-2 h-2" role="status" aria-label="실행 중">
                    <span className="absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75 animate-ping" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
                </div>
            );
        case 'done':
            return (
                <div
                    className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)] animate-scaleIn"
                    role="status"
                    aria-label="완료"
                />
            );
        case 'error':
            return (
                <div
                    className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"
                    role="status"
                    aria-label="오류"
                />
            );
        default:
            return (
                <div className="flex gap-1" aria-hidden="true">
                    <div className="w-1.5 h-1.5 rounded-full bg-white/10" />
                    <div className="w-1.5 h-1.5 rounded-full bg-white/10" />
                </div>
            );
    }
});

StatusIndicator.displayName = 'StatusIndicator';

// ============================================================
// Main Component
// ============================================================

export const NodeWrapper = memo(({
    children,
    title,
    colorClass,
    status = 'idle',
    isLocked = false,
    isVariableSlot = false,
    viralBadge,
    icon,
    errorMessage,
    className
}: NodeWrapperProps) => {
    const theme = detectTheme(colorClass);
    const headerGradient = THEME_GRADIENTS[theme];
    const ambientGlow = THEME_GLOWS[theme];

    // Interactive border styles
    const borderStyles = isLocked
        ? 'border-amber-400 shadow-[0_0_30px_rgba(251,191,36,0.15)]'
        : isVariableSlot
            ? 'border-pink-500 shadow-[0_0_25px_rgba(244,63,94,0.15)] ring-1 ring-pink-500/20'
            : 'hover:shadow-[0_0_30px_rgba(255,255,255,0.08)] hover:border-white/30';

    const pulsingClass = status === 'running' && !isLocked ? 'animate-pulse' : '';

    return (
        <div
            className={cn(
                // Base styles
                "glass-panel rounded-2xl overflow-visible border transition-all duration-200 group",
                // Responsive width
                "min-w-[280px] sm:min-w-[320px] max-w-[400px]",
                colorClass,
                borderStyles,
                pulsingClass,
                className
            )}
        >
            {/* Header */}
            <header className={cn(
                "px-5 py-3.5 border-b border-white/5 flex items-center justify-between",
                "bg-gradient-to-r backdrop-blur-md",
                headerGradient
            )}>
                <div className="flex items-center gap-2.5">
                    {icon}
                    {isLocked && (
                        <Lock
                            className="w-3.5 h-3.5 text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.8)]"
                            aria-hidden="true"
                        />
                    )}
                    {isVariableSlot && !isLocked && (
                        <Target
                            className="w-3.5 h-3.5 text-pink-400 drop-shadow-[0_0_8px_rgba(244,63,94,0.8)]"
                            aria-hidden="true"
                        />
                    )}
                    <h3 className="font-bold text-[11px] tracking-[0.15em] text-white/90 uppercase font-mono shadow-black/50 drop-shadow-sm">
                        {title}
                    </h3>
                    {isVariableSlot && !isLocked && (
                        <span className="text-[9px] px-2 py-0.5 bg-pink-500/10 text-pink-300 border border-pink-500/20 rounded-full font-bold">
                            EDIT
                        </span>
                    )}
                </div>

                <div className="flex gap-2 items-center">
                    {viralBadge && (
                        <span className="text-[9px] px-2 py-0.5 bg-gradient-to-r from-pink-500/20 to-purple-500/20 text-pink-200 border border-pink-500/30 rounded-full font-bold shadow-[0_0_15px_rgba(236,72,153,0.2)]">
                            {viralBadge}
                        </span>
                    )}
                    <div className="flex gap-1.5 pl-2 border-l border-white/10">
                        <StatusIndicator status={status} />
                    </div>
                </div>
            </header>

            {/* Error Banner */}
            {status === 'error' && errorMessage && (
                <div
                    className="px-4 py-2.5 bg-red-500/10 border-b border-red-500/20 text-[10px] text-red-300 font-mono flex items-center gap-2"
                    role="alert"
                >
                    <span aria-hidden="true">⚠️</span>
                    {errorMessage}
                </div>
            )}

            {/* Content Body */}
            <div className="p-5 bg-[#050505]/85 backdrop-blur-xl relative">
                {/* Grid Texture */}
                <div
                    className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.04] bg-[length:20px_20px] pointer-events-none mix-blend-overlay"
                    aria-hidden="true"
                />

                {/* Ambient Glow */}
                <div
                    className={cn(
                        "absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t opacity-10 pointer-events-none",
                        ambientGlow
                    )}
                    aria-hidden="true"
                />

                {/* Locked Warning */}
                {isLocked && (
                    <div className="mb-4 px-3 py-2 bg-amber-500/5 border border-amber-500/20 rounded-lg text-[10px] text-amber-300/80 text-center font-mono">
                        LOCKED :: MASTER NODE
                    </div>
                )}

                {/* Children */}
                <div className="relative z-10">
                    {children}
                </div>
            </div>
        </div>
    );
});

NodeWrapper.displayName = 'NodeWrapper';
