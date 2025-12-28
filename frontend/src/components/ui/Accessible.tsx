'use client';

/**
 * AccessibleComponents - 접근성 향상 컴포넌트 (PEGL v1.0)
 * 
 * WCAG 2.1 가이드라인 준수
 * - 키보드 네비게이션
 * - 스크린 리더 지원
 * - 포커스 관리
 */
import { forwardRef, useRef, useEffect, KeyboardEvent, ReactNode } from 'react';

/**
 * VisuallyHidden - 시각적으로 숨기되 스크린 리더에서 읽힘
 */
export function VisuallyHidden({ children }: { children: ReactNode }) {
    return (
        <span
            style={{
                border: 0,
                clip: 'rect(0 0 0 0)',
                height: '1px',
                margin: '-1px',
                overflow: 'hidden',
                padding: 0,
                position: 'absolute',
                width: '1px',
                whiteSpace: 'nowrap',
            }}
        >
            {children}
        </span>
    );
}

/**
 * SkipLink - 메인 콘텐츠로 건너뛰기 링크
 */
export function SkipLink({ targetId = 'main-content' }: { targetId?: string }) {
    return (
        <a
            href={`#${targetId}`}
            className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2 focus:bg-violet-600 focus:text-white focus:rounded-lg focus:font-medium"
        >
            메인 콘텐츠로 건너뛰기
        </a>
    );
}

/**
 * FocusTrap - 포커스를 특정 영역 내에 가둠 (모달용)
 */
interface FocusTrapProps {
    children: ReactNode;
    active?: boolean;
    className?: string;
}

export function FocusTrap({ children, active = true, className = '' }: FocusTrapProps) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!active) return;

        const container = containerRef.current;
        if (!container) return;

        const focusableElements = container.querySelectorAll<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        // 첫 포커스 가능 요소에 포커스
        firstElement.focus();

        const handleKeyDown = (e: globalThis.KeyboardEvent) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        };

        container.addEventListener('keydown', handleKeyDown);
        return () => container.removeEventListener('keydown', handleKeyDown);
    }, [active]);

    return (
        <div ref={containerRef} className={className}>
            {children}
        </div>
    );
}

/**
 * AccessibleButton - 접근성 향상 버튼
 */
interface AccessibleButtonProps {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    loading?: boolean;
    ariaLabel?: string;
    ariaDescribedBy?: string;
    className?: string;
    type?: 'button' | 'submit' | 'reset';
}

export const AccessibleButton = forwardRef<HTMLButtonElement, AccessibleButtonProps>(
    ({ children, onClick, disabled, loading, ariaLabel, ariaDescribedBy, className = '', type = 'button' }, ref) => {
        return (
            <button
                ref={ref}
                type={type}
                onClick={onClick}
                disabled={disabled || loading}
                aria-label={ariaLabel}
                aria-describedby={ariaDescribedBy}
                aria-busy={loading}
                aria-disabled={disabled}
                className={`focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
            >
                {loading ? (
                    <>
                        <span className="sr-only">로딩 중</span>
                        <span aria-hidden="true">
                            <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                        </span>
                    </>
                ) : (
                    children
                )}
            </button>
        );
    }
);
AccessibleButton.displayName = 'AccessibleButton';

/**
 * AccessibleLink - 접근성 향상 링크
 */
interface AccessibleLinkProps {
    children: ReactNode;
    href: string;
    external?: boolean;
    ariaLabel?: string;
    className?: string;
}

export function AccessibleLink({ children, href, external = false, ariaLabel, className = '' }: AccessibleLinkProps) {
    const externalProps = external
        ? {
            target: '_blank',
            rel: 'noopener noreferrer',
        }
        : {};

    return (
        <a
            href={href}
            aria-label={ariaLabel}
            className={`focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-black ${className}`}
            {...externalProps}
        >
            {children}
            {external && (
                <VisuallyHidden>(새 창에서 열림)</VisuallyHidden>
            )}
        </a>
    );
}

/**
 * LiveRegion - 스크린 리더에 동적 업데이트 알림
 */
interface LiveRegionProps {
    children: ReactNode;
    politeness?: 'polite' | 'assertive' | 'off';
    atomic?: boolean;
}

export function LiveRegion({ children, politeness = 'polite', atomic = true }: LiveRegionProps) {
    return (
        <div
            aria-live={politeness}
            aria-atomic={atomic}
            className="sr-only"
        >
            {children}
        </div>
    );
}

/**
 * Announcement - 스크린 리더 알림 (프로그래매틱)
 */
export function useAnnouncement() {
    const announce = (message: string, politeness: 'polite' | 'assertive' = 'polite') => {
        const element = document.createElement('div');
        element.setAttribute('role', 'status');
        element.setAttribute('aria-live', politeness);
        element.setAttribute('aria-atomic', 'true');
        element.className = 'sr-only';
        element.textContent = message;

        document.body.appendChild(element);

        setTimeout(() => {
            document.body.removeChild(element);
        }, 1000);
    };

    return { announce };
}

/**
 * KeyboardNavigable - 키보드 네비게이션 컨테이너
 */
interface KeyboardNavigableProps {
    children: ReactNode;
    onEnter?: () => void;
    onEscape?: () => void;
    onArrowUp?: () => void;
    onArrowDown?: () => void;
    onArrowLeft?: () => void;
    onArrowRight?: () => void;
    className?: string;
}

export function KeyboardNavigable({
    children,
    onEnter,
    onEscape,
    onArrowUp,
    onArrowDown,
    onArrowLeft,
    onArrowRight,
    className = '',
}: KeyboardNavigableProps) {
    const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
        switch (e.key) {
            case 'Enter':
                onEnter?.();
                break;
            case 'Escape':
                onEscape?.();
                break;
            case 'ArrowUp':
                e.preventDefault();
                onArrowUp?.();
                break;
            case 'ArrowDown':
                e.preventDefault();
                onArrowDown?.();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                onArrowLeft?.();
                break;
            case 'ArrowRight':
                e.preventDefault();
                onArrowRight?.();
                break;
        }
    };

    return (
        <div onKeyDown={handleKeyDown} className={className}>
            {children}
        </div>
    );
}

/**
 * FormField - 접근성 향상 폼 필드
 */
interface FormFieldProps {
    id: string;
    label: string;
    error?: string;
    hint?: string;
    required?: boolean;
    children: ReactNode;
    className?: string;
}

export function FormField({ id, label, error, hint, required, children, className = '' }: FormFieldProps) {
    const hintId = hint ? `${id}-hint` : undefined;
    const errorId = error ? `${id}-error` : undefined;
    const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined;

    return (
        <div className={className}>
            <label htmlFor={id} className="block text-sm font-medium text-white mb-1">
                {label}
                {required && <span className="text-red-400 ml-1" aria-hidden="true">*</span>}
                {required && <VisuallyHidden>(필수)</VisuallyHidden>}
            </label>

            {hint && (
                <p id={hintId} className="text-xs text-white/50 mb-2">
                    {hint}
                </p>
            )}

            <div aria-describedby={describedBy}>
                {children}
            </div>

            {error && (
                <p id={errorId} className="text-xs text-red-400 mt-1" role="alert">
                    {error}
                </p>
            )}
        </div>
    );
}

export default {
    VisuallyHidden,
    SkipLink,
    FocusTrap,
    AccessibleButton,
    AccessibleLink,
    LiveRegion,
    useAnnouncement,
    KeyboardNavigable,
    FormField,
};
