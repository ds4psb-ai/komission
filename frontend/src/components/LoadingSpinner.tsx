'use client';

/**
 * LoadingSpinner - 로딩 표시 컴포넌트 (PEGL v1.0)
 * 
 * 다양한 크기와 스타일 지원
 */

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg' | 'xl';
    className?: string;
    label?: string;
}

const SIZE_CONFIG = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3',
    xl: 'w-12 h-12 border-4',
};

export function LoadingSpinner({ size = 'md', className = '', label }: LoadingSpinnerProps) {
    return (
        <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
            <div
                className={`${SIZE_CONFIG[size]} border-white/20 border-t-violet-500 rounded-full animate-spin`}
            />
            {label && (
                <span className="text-sm text-white/50">{label}</span>
            )}
        </div>
    );
}

/**
 * PageLoader - 전체 페이지 로딩
 */
export function PageLoader({ label = '로딩 중...' }: { label?: string }) {
    return (
        <div className="min-h-[50vh] flex items-center justify-center">
            <LoadingSpinner size="xl" label={label} />
        </div>
    );
}

/**
 * InlineLoader - 인라인 로딩
 */
export function InlineLoader({ label }: { label?: string }) {
    return (
        <div className="flex items-center gap-2 text-white/50">
            <LoadingSpinner size="sm" />
            {label && <span className="text-sm">{label}</span>}
        </div>
    );
}

/**
 * ButtonLoader - 버튼 내부 로딩
 */
export function ButtonLoader() {
    return (
        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
    );
}

/**
 * CardLoader - 카드 로딩 상태
 */
export function CardLoader({ count = 4 }: { count?: number }) {
    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="bg-white/5 rounded-2xl overflow-hidden animate-pulse">
                    <div className="aspect-[4/5] bg-white/5" />
                    <div className="p-4 space-y-3">
                        <div className="h-4 bg-white/10 rounded w-3/4" />
                        <div className="h-3 bg-white/5 rounded w-1/2" />
                    </div>
                </div>
            ))}
        </div>
    );
}

export default LoadingSpinner;
