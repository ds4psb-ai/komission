/**
 * MCP React Hooks
 * AI 분석 및 MCP 리소스 조회를 위한 React 훅
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { mcpClient, AIAnalysisResult, BatchAnalysisResult, SearchResponse, ToolCallResult } from './mcp-client';

// 공통 상태 타입
interface MCPState<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
}

import { useTranslations } from 'next-intl';

const useIsMountedRef = () => {
    const isMountedRef = useRef(true);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    return isMountedRef;
};

/**
 * AI 패턴 분석 훅
 * smart_pattern_analysis 도구를 호출하여 AI 분석 결과를 얻습니다.
 */
export function useAIAnalysis() {
    const isMountedRef = useIsMountedRef();
    const t = useTranslations('hooks.mcp');
    const [state, setState] = useState<MCPState<AIAnalysisResult>>({
        data: null,
        loading: false,
        error: null,
    });

    const analyze = useCallback(async (
        outlierId: string,
        analysisType: 'recommendation' | 'shooting_guide' | 'risk' = 'recommendation'
    ) => {
        setState({ data: null, loading: true, error: null });

        try {
            const result = await mcpClient.analyzePattern(outlierId, analysisType);
            if (!isMountedRef.current) return;

            if (result.success && result.data) {
                setState({ data: result.data, loading: false, error: null });
            } else {
                setState({ data: null, loading: false, error: result.error || t('analysisFailed') });
            }
        } catch (err) {
            if (!isMountedRef.current) return;
            setState({
                data: null,
                loading: false,
                error: err instanceof Error ? err.message : t('unknownError'),
            });
        }
    }, [isMountedRef]);

    const reset = useCallback(() => {
        if (isMountedRef.current) {
            setState({ data: null, loading: false, error: null });
        }
    }, [isMountedRef]);

    return {
        ...state,
        analyze,
        reset,
    };
}

/**
 * AI 배치 분석 훅
 * ai_batch_analysis 도구를 호출하여 여러 패턴의 트렌드를 분석합니다.
 */
export function useBatchAnalysis() {
    const isMountedRef = useIsMountedRef();
    const t = useTranslations('hooks.mcp');
    const [state, setState] = useState<MCPState<BatchAnalysisResult>>({
        data: null,
        loading: false,
        error: null,
    });

    const analyze = useCallback(async (
        outlierIds: string[],
        focus: 'trends' | 'comparison' | 'strategy' = 'trends'
    ) => {
        if (outlierIds.length < 2) {
            setState({ data: null, loading: false, error: t('minOutliers') });
            return;
        }

        if (outlierIds.length > 10) {
            setState({ data: null, loading: false, error: t('maxOutliers') });
            return;
        }

        setState({ data: null, loading: true, error: null });

        try {
            const result = await mcpClient.batchAnalysis(outlierIds, focus);
            if (!isMountedRef.current) return;

            if (result.success && result.data) {
                setState({ data: result.data, loading: false, error: null });
            } else {
                setState({ data: null, loading: false, error: result.error || 'Batch analysis failed' });
            }
        } catch (err) {
            if (!isMountedRef.current) return;
            setState({
                data: null,
                loading: false,
                error: err instanceof Error ? err.message : 'Unknown error',
            });
        }
    }, [isMountedRef]);

    const reset = useCallback(() => {
        if (isMountedRef.current) {
            setState({ data: null, loading: false, error: null });
        }
    }, [isMountedRef]);

    return {
        ...state,
        analyze,
        reset,
    };
}

/**
 * 패턴 검색 훅
 */
export function usePatternSearch() {
    const isMountedRef = useIsMountedRef();
    const t = useTranslations('hooks.mcp');
    const [state, setState] = useState<MCPState<SearchResponse>>({
        data: null,
        loading: false,
        error: null,
    });

    const search = useCallback(async (
        query: string,
        options?: {
            category?: string;
            platform?: string;
            minTier?: string;
            limit?: number;
        }
    ) => {
        setState({ data: null, loading: true, error: null });

        try {
            const result = await mcpClient.searchPatterns(query, {
                ...options,
                outputFormat: 'json',
            }) as ToolCallResult<SearchResponse>;
            if (!isMountedRef.current) return;

            if (result.success && result.data) {
                setState({ data: result.data, loading: false, error: null });
            } else {
                setState({ data: null, loading: false, error: result.error || 'Search failed' });
            }
        } catch (err) {
            if (!isMountedRef.current) return;
            setState({
                data: null,
                loading: false,
                error: err instanceof Error ? err.message : 'Unknown error',
            });
        }
    }, [isMountedRef]);

    const reset = useCallback(() => {
        if (isMountedRef.current) {
            setState({ data: null, loading: false, error: null });
        }
    }, [isMountedRef]);

    return {
        ...state,
        search,
        reset,
    };
}

/**
 * MCP 리소스 조회 훅
 */
export function useMCPResource() {
    const isMountedRef = useIsMountedRef();
    const t = useTranslations('hooks.mcp');
    const [state, setState] = useState<MCPState<string>>({
        data: null,
        loading: false,
        error: null,
    });

    const fetch = useCallback(async (
        resourceType: 'pattern' | 'comments' | 'vdg' | 'director-pack',
        id: string
    ) => {
        setState({ data: null, loading: true, error: null });

        try {
            let result: ToolCallResult<string>;

            switch (resourceType) {
                case 'pattern':
                    result = await mcpClient.getPattern(id);
                    break;
                case 'comments':
                    result = await mcpClient.getComments(id);
                    break;
                case 'vdg':
                    result = await mcpClient.getVDG(id);
                    break;
                case 'director-pack':
                    result = await mcpClient.getDirectorPack(id);
                    break;
            }

            if (!isMountedRef.current) return;
            if (result.success && result.data) {
                setState({ data: result.data, loading: false, error: null });
            } else {
                setState({ data: null, loading: false, error: result.error || 'Resource fetch failed' });
            }
        } catch (err) {
            if (!isMountedRef.current) return;
            setState({
                data: null,
                loading: false,
                error: err instanceof Error ? err.message : 'Unknown error',
            });
        }
    }, [isMountedRef]);

    const reset = useCallback(() => {
        if (isMountedRef.current) {
            setState({ data: null, loading: false, error: null });
        }
    }, [isMountedRef]);

    return {
        ...state,
        fetch,
        reset,
    };
}

/**
 * MCP 서버 연결 상태 훅
 */
export function useMCPConnection() {
    const isMountedRef = useIsMountedRef();
    const [connected, setConnected] = useState<boolean | null>(null);
    const [checking, setChecking] = useState(false);

    const check = useCallback(async () => {
        setChecking(true);
        try {
            const isConnected = await mcpClient.ping();
            if (!isMountedRef.current) return;
            setConnected(isConnected);
        } catch {
            if (!isMountedRef.current) return;
            setConnected(false);
        } finally {
            if (isMountedRef.current) {
                setChecking(false);
            }
        }
    }, [isMountedRef]);

    return {
        connected,
        checking,
        check,
    };
}
