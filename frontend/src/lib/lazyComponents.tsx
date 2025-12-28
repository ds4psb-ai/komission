'use client';

/**
 * LazyComponents - 코드 분할을 위한 지연 로딩 컴포넌트 (PEGL v1.0)
 * 
 * 무거운 컴포넌트를 지연 로딩하여 초기 번들 크기 최소화
 */
import dynamic from 'next/dynamic';
import { ComponentType, ReactNode } from 'react';

// 로딩 스피너
const LoadingSpinner = () => (
    <div className="flex items-center justify-center p-8">
        <div className="w-8 h-8 border-2 border-white/20 border-t-violet-500 rounded-full animate-spin" />
    </div>
);

// 카드 로딩 스켈레톤
const CardSkeleton = () => (
    <div className="bg-white/5 rounded-2xl overflow-hidden animate-pulse">
        <div className="aspect-[4/5] bg-white/5" />
        <div className="p-4 space-y-3">
            <div className="h-4 bg-white/10 rounded w-3/4" />
            <div className="h-3 bg-white/5 rounded w-1/2" />
        </div>
    </div>
);

// 패널 로딩 스켈레톤
const PanelSkeleton = () => (
    <div className="bg-white/5 rounded-2xl p-6 animate-pulse space-y-4">
        <div className="h-6 bg-white/10 rounded w-1/3" />
        <div className="h-4 bg-white/5 rounded w-2/3" />
        <div className="h-4 bg-white/5 rounded w-1/2" />
    </div>
);

/**
 * 무거운 컴포넌트 지연 로딩
 */

// React Flow Canvas (매우 무거움)
export const LazyReactFlowCanvas = dynamic(
    () => import('@/app/canvas/page').then(mod => ({ default: mod.default })),
    {
        loading: () => <LoadingSpinner />,
        ssr: false  // React Flow는 SSR 비활성화 필요
    }
);

// Framer Motion 의존 컴포넌트들
export const LazyGenealogyWidget = dynamic(
    () => import('@/components/GenealogyWidget').then(mod => ({ default: mod.GenealogyWidget })),
    { loading: () => <PanelSkeleton /> }
);

// 차트 컴포넌트 (필요시)
export const LazyPatternConfidenceChart = dynamic(
    () => import('@/components/PatternConfidenceChart').then(mod => ({ default: mod.PatternConfidenceChart })),
    { loading: () => <PanelSkeleton /> }
);

// 무거운 모달들
export const LazyCelebrationModal = dynamic(
    () => import('@/components/CelebrationModal').then(mod => ({ default: mod.CelebrationModal })),
    { ssr: false }
);

// 템플릿 갤러리
export const LazyTemplateGallery = dynamic(
    () => import('@/components/TemplateGallery').then(mod => ({ default: mod.TemplateGallery })),
    { loading: () => <CardSkeleton /> }
);

/**
 * withLazyLoad - HOC for lazy loading any component
 */
export function withLazyLoad<P extends object>(
    importFn: () => Promise<{ default: ComponentType<P> }>,
    LoadingComponent: ReactNode = <LoadingSpinner />
) {
    return dynamic(importFn, {
        loading: () => <>{LoadingComponent}</>,
    });
}

/**
 * DeferredRender - 초기 렌더링 이후 지연 렌더링
 */
export function DeferredRender({
    children,
    delay = 100
}: {
    children: ReactNode;
    delay?: number
}) {
    const [show, setShow] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => setShow(true), delay);
        return () => clearTimeout(timer);
    }, [delay]);

    if (!show) return null;
    return <>{children}</>;
}

// useState, useEffect import
import { useState, useEffect } from 'react';

export default {
    LazyReactFlowCanvas,
    LazyGenealogyWidget,
    LazyPatternConfidenceChart,
    LazyCelebrationModal,
    LazyTemplateGallery,
    withLazyLoad,
    DeferredRender,
};
