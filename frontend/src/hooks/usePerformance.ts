import { useState, useEffect, useRef, useCallback, useMemo } from 'react';

/**
 * useDebounce - 값 디바운스 (PEGL v1.0)
 * 
 * 검색 입력 등 빠른 변화에 지연 적용
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => clearTimeout(timer);
    }, [value, delay]);

    return debouncedValue;
}

/**
 * useDebouncedCallback - 콜백 디바운스
 */
export function useDebouncedCallback<T extends (...args: Parameters<T>) => void>(
    callback: T,
    delay: number = 300
): T {
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);
    const callbackRef = useRef(callback);

    // 항상 최신 콜백 참조
    useEffect(() => {
        callbackRef.current = callback;
    }, [callback]);

    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
            }
        };
    }, []);

    return useCallback(
        ((...args: Parameters<T>) => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
            timeoutRef.current = setTimeout(() => {
                callbackRef.current(...args);
            }, delay);
        }) as T,
        [delay]
    );
}

/**
 * useThrottle - 값 스로틀
 * 
 * 스크롤 이벤트 등 빈번한 업데이트에 제한 적용
 */
export function useThrottle<T>(value: T, limit: number = 200): T {
    const [throttledValue, setThrottledValue] = useState<T>(value);
    const lastRan = useRef<number>(Date.now());

    useEffect(() => {
        const now = Date.now();

        if (now - lastRan.current >= limit) {
            setThrottledValue(value);
            lastRan.current = now;
        } else {
            const timer = setTimeout(() => {
                setThrottledValue(value);
                lastRan.current = Date.now();
            }, limit - (now - lastRan.current));

            return () => clearTimeout(timer);
        }
    }, [value, limit]);

    return throttledValue;
}

/**
 * useThrottledCallback - 콜백 스로틀
 */
export function useThrottledCallback<T extends (...args: Parameters<T>) => void>(
    callback: T,
    limit: number = 200
): T {
    const lastRan = useRef<number>(0);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);
    const callbackRef = useRef(callback);

    useEffect(() => {
        callbackRef.current = callback;
    }, [callback]);

    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
            }
        };
    }, []);

    return useCallback(
        ((...args: Parameters<T>) => {
            const now = Date.now();

            if (now - lastRan.current >= limit) {
                callbackRef.current(...args);
                lastRan.current = now;
            } else {
                if (timeoutRef.current) {
                    clearTimeout(timeoutRef.current);
                }
                timeoutRef.current = setTimeout(() => {
                    callbackRef.current(...args);
                    lastRan.current = Date.now();
                }, limit - (now - lastRan.current));
            }
        }) as T,
        [limit]
    );
}

/**
 * useIntersectionObserver - 요소 가시성 감지
 * 
 * 무한 스크롤, 지연 로딩에 사용
 */
export function useIntersectionObserver(
    options?: IntersectionObserverInit
): [React.RefObject<HTMLDivElement | null>, boolean] {
    const ref = useRef<HTMLDivElement>(null);
    const [isIntersecting, setIsIntersecting] = useState(false);

    useEffect(() => {
        const element = ref.current;
        if (!element) return;

        const observer = new IntersectionObserver(([entry]) => {
            setIsIntersecting(entry.isIntersecting);
        }, options);

        observer.observe(element);

        return () => observer.disconnect();
    }, [options]);

    return [ref, isIntersecting];
}

/**
 * useLazyLoad - 지연 로딩 훅
 * 
 * 컴포넌트가 뷰포트에 들어올 때만 렌더링
 */
export function useLazyLoad(threshold: number = 0.1): {
    ref: React.RefObject<HTMLDivElement | null>;
    shouldLoad: boolean;
} {
    const options = useMemo(() => ({ threshold }), [threshold]);
    const [ref, isIntersecting] = useIntersectionObserver(options);
    const [shouldLoad, setShouldLoad] = useState(false);

    useEffect(() => {
        if (isIntersecting && !shouldLoad) {
            setShouldLoad(true);
        }
    }, [isIntersecting, shouldLoad]);

    return { ref, shouldLoad };
}

/**
 * useWindowSize - 윈도우 크기 감지 (throttled)
 */
export function useWindowSize() {
    const [size, setSize] = useState({
        width: typeof window !== 'undefined' ? window.innerWidth : 0,
        height: typeof window !== 'undefined' ? window.innerHeight : 0,
    });

    const handleResize = useThrottledCallback(() => {
        setSize({
            width: window.innerWidth,
            height: window.innerHeight,
        });
    }, 100);

    useEffect(() => {
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [handleResize]);

    return size;
}

/**
 * useLocalStorage - 로컬 스토리지 동기화
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((prev: T) => T)) => void] {
    const [storedValue, setStoredValue] = useState<T>(() => {
        if (typeof window === 'undefined') return initialValue;

        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch {
            return initialValue;
        }
    });

    const setValue = useCallback((value: T | ((prev: T) => T)) => {
        setStoredValue(prev => {
            const valueToStore = value instanceof Function ? value(prev) : value;

            if (typeof window !== 'undefined') {
                localStorage.setItem(key, JSON.stringify(valueToStore));
            }

            return valueToStore;
        });
    }, [key]);

    return [storedValue, setValue];
}

export default {
    useDebounce,
    useDebouncedCallback,
    useThrottle,
    useThrottledCallback,
    useIntersectionObserver,
    useLazyLoad,
    useWindowSize,
    useLocalStorage,
};
