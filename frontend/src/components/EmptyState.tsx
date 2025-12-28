'use client';

/**
 * EmptyState - 빈 상태 표시 컴포넌트 (PEGL v1.0)
 * 
 * 데이터가 없을 때 사용자에게 명확한 메시지와 액션을 제공
 */
import Link from 'next/link';
import {
    Search, FileQuestion, Inbox, Database,
    PlusCircle, ArrowRight, RefreshCw, Home
} from 'lucide-react';

type EmptyStateVariant = 'default' | 'search' | 'error' | 'no-data' | 'no-access';

interface EmptyStateAction {
    label: string;
    href?: string;
    onClick?: () => void;
    variant?: 'primary' | 'secondary';
}

interface EmptyStateProps {
    variant?: EmptyStateVariant;
    icon?: React.ReactNode;
    title: string;
    description?: string;
    actions?: EmptyStateAction[];
    className?: string;
}

const VARIANT_CONFIG = {
    default: {
        icon: <Inbox className="w-12 h-12" />,
        color: 'text-white/30',
        bg: 'bg-white/5',
    },
    search: {
        icon: <Search className="w-12 h-12" />,
        color: 'text-violet-400/50',
        bg: 'bg-violet-500/5',
    },
    error: {
        icon: <FileQuestion className="w-12 h-12" />,
        color: 'text-red-400/50',
        bg: 'bg-red-500/5',
    },
    'no-data': {
        icon: <Database className="w-12 h-12" />,
        color: 'text-cyan-400/50',
        bg: 'bg-cyan-500/5',
    },
    'no-access': {
        icon: <FileQuestion className="w-12 h-12" />,
        color: 'text-amber-400/50',
        bg: 'bg-amber-500/5',
    },
};

export function EmptyState({
    variant = 'default',
    icon,
    title,
    description,
    actions = [],
    className = '',
}: EmptyStateProps) {
    const config = VARIANT_CONFIG[variant];

    return (
        <div className={`flex flex-col items-center justify-center py-16 px-6 text-center ${config.bg} rounded-2xl border border-white/5 ${className}`}>
            {/* Icon */}
            <div className={`mb-6 ${config.color}`}>
                {icon || config.icon}
            </div>

            {/* Title */}
            <h3 className="text-xl font-bold text-white mb-2">{title}</h3>

            {/* Description */}
            {description && (
                <p className="text-sm text-white/50 max-w-md mb-6">{description}</p>
            )}

            {/* Actions */}
            {actions.length > 0 && (
                <div className="flex flex-wrap items-center justify-center gap-3">
                    {actions.map((action, idx) => {
                        const isPrimary = action.variant === 'primary';
                        const baseClass = isPrimary
                            ? 'px-5 py-2.5 bg-violet-500 hover:bg-violet-400 text-white font-bold rounded-xl transition-colors'
                            : 'px-5 py-2.5 bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 rounded-xl transition-colors';

                        if (action.href) {
                            return (
                                <Link key={idx} href={action.href} className={`flex items-center gap-2 ${baseClass}`}>
                                    {isPrimary && <PlusCircle className="w-4 h-4" />}
                                    {action.label}
                                    {!isPrimary && <ArrowRight className="w-4 h-4" />}
                                </Link>
                            );
                        }

                        return (
                            <button
                                key={idx}
                                onClick={action.onClick}
                                className={`flex items-center gap-2 ${baseClass}`}
                            >
                                {action.label === '새로고침' && <RefreshCw className="w-4 h-4" />}
                                {action.label === '홈으로' && <Home className="w-4 h-4" />}
                                {action.label}
                            </button>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

/**
 * NoResults - 검색 결과 없음 (간단한 버전)
 */
export function NoResults({ query, onReset }: { query?: string; onReset?: () => void }) {
    return (
        <EmptyState
            variant="search"
            title="검색 결과가 없습니다"
            description={query ? `"${query}"에 대한 결과를 찾을 수 없습니다.` : '검색어를 입력해주세요.'}
            actions={onReset ? [{ label: '필터 초기화', onClick: onReset, variant: 'secondary' }] : []}
        />
    );
}

/**
 * ErrorState - 에러 상태 (간단한 버전)
 */
export function ErrorState({
    message = '문제가 발생했습니다',
    onRetry
}: {
    message?: string;
    onRetry?: () => void
}) {
    return (
        <EmptyState
            variant="error"
            title="오류 발생"
            description={message}
            actions={[
                ...(onRetry ? [{ label: '다시 시도', onClick: onRetry, variant: 'primary' as const }] : []),
                { label: '홈으로', href: '/', variant: 'secondary' as const },
            ]}
        />
    );
}

/**
 * NoAccess - 접근 권한 없음
 */
export function NoAccess({ message }: { message?: string }) {
    return (
        <EmptyState
            variant="no-access"
            title="접근 권한이 없습니다"
            description={message || '이 페이지를 보려면 로그인이 필요합니다.'}
            actions={[
                { label: '로그인', href: '/login', variant: 'primary' },
                { label: '홈으로', href: '/', variant: 'secondary' },
            ]}
        />
    );
}

export default EmptyState;
