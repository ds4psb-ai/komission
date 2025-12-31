/**
 * SimpleCache - 간단한 메모리 캐시 (PEGL v1.0)
 * 
 * API 응답 캐싱으로 불필요한 네트워크 요청 감소
 */

interface CacheEntry<T> {
    data: T;
    timestamp: number;
    expiresAt: number;
}

class SimpleCache {
    private cache = new Map<string, CacheEntry<unknown>>();
    private defaultTTL = 5 * 60 * 1000; // 5분 기본

    /**
     * 캐시에서 데이터 가져오기
     */
    get<T>(key: string): T | null {
        const entry = this.cache.get(key);
        if (!entry) return null;

        // 만료 확인
        if (Date.now() > entry.expiresAt) {
            this.cache.delete(key);
            return null;
        }

        return entry.data as T;
    }

    /**
     * 캐시에 데이터 저장
     */
    set<T>(key: string, data: T, ttl?: number): void {
        const now = Date.now();
        this.cache.set(key, {
            data,
            timestamp: now,
            expiresAt: now + (ttl ?? this.defaultTTL),
        });
    }

    /**
     * 특정 키 삭제
     */
    delete(key: string): void {
        this.cache.delete(key);
    }

    /**
     * 패턴으로 삭제 (예: 'outliers:*')
     */
    deleteByPattern(pattern: string): void {
        const escaped = pattern
            .split('*')
            .map(part => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
            .join('.*');
        const regex = new RegExp('^' + escaped);
        for (const key of this.cache.keys()) {
            if (regex.test(key)) {
                this.cache.delete(key);
            }
        }
    }

    /**
     * 전체 캐시 클리어
     */
    clear(): void {
        this.cache.clear();
    }

    /**
     * 캐시 통계
     */
    stats() {
        let validCount = 0;
        let expiredCount = 0;
        const now = Date.now();

        for (const entry of this.cache.values()) {
            if (now > entry.expiresAt) {
                expiredCount++;
            } else {
                validCount++;
            }
        }

        return {
            total: this.cache.size,
            valid: validCount,
            expired: expiredCount,
        };
    }

    /**
     * 만료된 항목 정리
     */
    cleanup(): number {
        let removed = 0;
        const now = Date.now();

        for (const [key, entry] of this.cache.entries()) {
            if (now > entry.expiresAt) {
                this.cache.delete(key);
                removed++;
            }
        }

        return removed;
    }
}

// 싱글톤 인스턴스
export const apiCache = new SimpleCache();

/**
 * 캐시된 fetch 래퍼
 */
export async function cachedFetch<T>(
    key: string,
    fetchFn: () => Promise<T>,
    options?: {
        ttl?: number;       // 밀리초
        force?: boolean;    // 캐시 무시하고 강제 fetch
    }
): Promise<T> {
    const { ttl, force = false } = options || {};

    // 캐시 확인
    if (!force) {
        const cached = apiCache.get<T>(key);
        if (cached !== null) {
            return cached;
        }
    }

    // 새로 fetch
    const data = await fetchFn();

    // 캐시에 저장
    apiCache.set(key, data, ttl);

    return data;
}

/**
 * SWR 스타일 stale-while-revalidate
 */
export async function staleWhileRevalidate<T>(
    key: string,
    fetchFn: () => Promise<T>,
    options?: {
        staleTime?: number;  // stale 상태 시간
        maxAge?: number;     // 최대 캐시 시간
    }
): Promise<{ data: T; isStale: boolean }> {
    const { staleTime = 60 * 1000, maxAge = 5 * 60 * 1000 } = options || {};
    const now = Date.now();

    const cached = apiCache.get<T>(key);
    const entry = (apiCache as any).cache.get(key) as CacheEntry<T> | undefined;

    // 캐시 없음 - 새로 fetch
    if (cached === null || !entry) {
        const data = await fetchFn();
        apiCache.set(key, data, maxAge);
        return { data, isStale: false };
    }

    // 캐시 있고 fresh
    if (now - entry.timestamp < staleTime) {
        return { data: cached, isStale: false };
    }

    // 캐시 있지만 stale - 반환하고 백그라운드에서 revalidate
    fetchFn().then(newData => {
        apiCache.set(key, newData, maxAge);
    }).catch(console.error);

    return { data: cached, isStale: true };
}

// 자동 정리 (5분마다)
if (typeof window !== 'undefined') {
    setInterval(() => {
        apiCache.cleanup();
    }, 5 * 60 * 1000);
}

export default apiCache;
