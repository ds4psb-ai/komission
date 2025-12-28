'use client';

/**
 * Skeleton Components (PEGL v1.0)
 * 
 * 로딩 상태를 위한 스켈레톤 컴포넌트
 */
import { cn } from '@/lib/utils';

interface SkeletonProps {
    className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
    return (
        <div
            className={cn(
                "animate-pulse rounded-lg bg-white/5",
                className
            )}
        />
    );
}

/**
 * VideoCardSkeleton - 비디오 카드 로딩
 */
export function VideoCardSkeleton() {
    return (
        <div className="bg-[#111] rounded-2xl overflow-hidden border border-white/5">
            {/* Thumbnail */}
            <Skeleton className="aspect-[9/16] w-full" />

            {/* Content */}
            <div className="p-4 space-y-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
                <div className="flex gap-2">
                    <Skeleton className="h-5 w-16 rounded-full" />
                    <Skeleton className="h-5 w-12 rounded-full" />
                </div>
            </div>
        </div>
    );
}

/**
 * StatsCardSkeleton - 통계 카드 로딩
 */
export function StatsCardSkeleton() {
    return (
        <div className="p-5 bg-white/5 border border-white/10 rounded-2xl">
            <div className="flex items-center gap-2 mb-2">
                <Skeleton className="w-4 h-4 rounded" />
                <Skeleton className="h-3 w-12" />
            </div>
            <Skeleton className="h-8 w-16 mb-2" />
            <Skeleton className="h-3 w-24" />
        </div>
    );
}

/**
 * ListItemSkeleton - 리스트 아이템 로딩
 */
export function ListItemSkeleton() {
    return (
        <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <Skeleton className="w-10 h-10 rounded-lg" />
                <div className="space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-24" />
                </div>
            </div>
            <Skeleton className="h-6 w-20 rounded-full" />
        </div>
    );
}

/**
 * TableSkeleton - 테이블 로딩
 */
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="divide-y divide-white/5">
            {Array.from({ length: rows }).map((_, i) => (
                <ListItemSkeleton key={i} />
            ))}
        </div>
    );
}

/**
 * CardGridSkeleton - 카드 그리드 로딩
 */
export function CardGridSkeleton({ count = 8, cols = 4 }: { count?: number; cols?: number }) {
    const colsClass = {
        2: 'grid-cols-2',
        3: 'grid-cols-2 md:grid-cols-3',
        4: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4',
        5: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5',
    }[cols] || 'grid-cols-2 md:grid-cols-4';

    return (
        <div className={cn("grid gap-4", colsClass)}>
            {Array.from({ length: count }).map((_, i) => (
                <VideoCardSkeleton key={i} />
            ))}
        </div>
    );
}

/**
 * PageSkeleton - 전체 페이지 로딩
 */
export function PageSkeleton() {
    return (
        <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="space-y-2">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-10 w-24 rounded-xl" />
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <StatsCardSkeleton key={i} />
                ))}
            </div>

            {/* Content */}
            <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                <div className="px-6 py-4 border-b border-white/5">
                    <Skeleton className="h-5 w-32" />
                </div>
                <TableSkeleton rows={5} />
            </div>
        </div>
    );
}

export default Skeleton;
