/**
 * STPF React Hooks
 * 
 * STPF v3.1 API 연동 훅:
 * - useSTPFQuickScore: 빠른 점수 계산
 * - useSTPFAnalysis: 전체 분석
 * - useSTPFGrade: 등급 조회
 * - useSTPFKelly: Kelly 의사결정
 */
'use client';

import { useState, useCallback, useEffect } from 'react';
import { api, STPFGradeResponse, STPFKellyResponse, STPFAnalyzeResponse, STPFQuickScoreResponse } from '@/lib/api';

// ==================
// useSTPFQuickScore
// ==================

interface STPFQuickScoreInput {
    essence: number;
    novelty: number;
    proof: number;
    risk: number;
    network: number;
}

interface UseSTPFQuickScoreReturn {
    data: STPFQuickScoreResponse | null;
    loading: boolean;
    error: string | null;
    calculate: (input: STPFQuickScoreInput) => Promise<void>;
    reset: () => void;
}

export function useSTPFQuickScore(): UseSTPFQuickScoreReturn {
    const [data, setData] = useState<STPFQuickScoreResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const calculate = useCallback(async (input: STPFQuickScoreInput) => {
        setLoading(true);
        setError(null);

        try {
            const result = await api.stpfQuickScore(input);
            setData(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'STPF 계산 실패');
            setData(null);
        } finally {
            setLoading(false);
        }
    }, []);

    const reset = useCallback(() => {
        setData(null);
        setError(null);
    }, []);

    return { data, loading, error, calculate, reset };
}

// ==================
// useSTPFGrade
// ==================

interface UseSTPFGradeReturn {
    grade: STPFGradeResponse | null;
    loading: boolean;
    error: string | null;
    fetch: (score: number) => Promise<void>;
}

export function useSTPFGrade(): UseSTPFGradeReturn {
    const [grade, setGrade] = useState<STPFGradeResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetch = useCallback(async (score: number) => {
        if (score < 0 || score > 1000) {
            setError('점수는 0-1000 사이여야 합니다');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const result = await api.stpfGetGrade(score);
            setGrade(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : '등급 조회 실패');
            setGrade(null);
        } finally {
            setLoading(false);
        }
    }, []);

    return { grade, loading, error, fetch };
}

// ==================
// useSTPFKelly
// ==================

interface UseSTPFKellyReturn {
    decision: STPFKellyResponse | null;
    loading: boolean;
    error: string | null;
    calculate: (score: number, timeHours?: number, viewMultiplier?: number) => Promise<void>;
}

export function useSTPFKelly(): UseSTPFKellyReturn {
    const [decision, setDecision] = useState<STPFKellyResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const calculate = useCallback(async (
        score: number,
        timeHours: number = 10,
        viewMultiplier: number = 3
    ) => {
        setLoading(true);
        setError(null);

        try {
            const result = await api.stpfKellyDecision(score, timeHours, viewMultiplier);
            setDecision(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Kelly 계산 실패');
            setDecision(null);
        } finally {
            setLoading(false);
        }
    }, []);

    return { decision, loading, error, calculate };
}

// ==================
// useSTPFAnalysis (Combined)
// ==================

interface STPFAnalysisState {
    score: number | null;
    signal: 'GO' | 'CONSIDER' | 'NO-GO' | null;
    grade: STPFGradeResponse | null;
    kelly: STPFKellyResponse | null;
    why: string | null;
    how: string[];
    loading: boolean;
    error: string | null;
}

interface UseSTPFAnalysisReturn extends STPFAnalysisState {
    analyzeQuick: (input: STPFQuickScoreInput) => Promise<void>;
    analyzeFromScore: (score: number) => Promise<void>;
    reset: () => void;
}

export function useSTPFAnalysis(): UseSTPFAnalysisReturn {
    const [state, setState] = useState<STPFAnalysisState>({
        score: null,
        signal: null,
        grade: null,
        kelly: null,
        why: null,
        how: [],
        loading: false,
        error: null,
    });

    const analyzeQuick = useCallback(async (input: STPFQuickScoreInput) => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            // 1. Get quick score
            const quickResult = await api.stpfQuickScore(input);
            const score = quickResult.score_1000;

            // 2. Get grade
            const gradeResult = await api.stpfGetGrade(score);

            // 3. Get Kelly decision
            const kellyResult = await api.stpfKellyDecision(score);

            setState({
                score: score,
                signal: quickResult.go_nogo as 'GO' | 'CONSIDER' | 'NO-GO',
                grade: gradeResult,
                kelly: kellyResult,
                why: quickResult.why,
                how: quickResult.how || [],
                loading: false,
                error: null,
            });
        } catch (err) {
            setState(prev => ({
                ...prev,
                loading: false,
                error: err instanceof Error ? err.message : 'STPF 분석 실패',
            }));
        }
    }, []);

    const analyzeFromScore = useCallback(async (score: number) => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            // 1. Get grade
            const gradeResult = await api.stpfGetGrade(score);

            // 2. Get Kelly decision
            const kellyResult = await api.stpfKellyDecision(score);

            // Determine signal from score
            let signal: 'GO' | 'CONSIDER' | 'NO-GO' = 'CONSIDER';
            if (score >= 600) signal = 'GO';
            else if (score < 400) signal = 'NO-GO';

            setState({
                score: score,
                signal: signal,
                grade: gradeResult,
                kelly: kellyResult,
                why: null,
                how: [],
                loading: false,
                error: null,
            });
        } catch (err) {
            setState(prev => ({
                ...prev,
                loading: false,
                error: err instanceof Error ? err.message : 'STPF 분석 실패',
            }));
        }
    }, []);

    const reset = useCallback(() => {
        setState({
            score: null,
            signal: null,
            grade: null,
            kelly: null,
            why: null,
            how: [],
            loading: false,
            error: null,
        });
    }, []);

    return {
        ...state,
        analyzeQuick,
        analyzeFromScore,
        reset,
    };
}

// ==================
// useSTPFFromVDG
// ==================

interface UseSTPFFromVDGReturn {
    data: STPFAnalyzeResponse | null;
    loading: boolean;
    error: string | null;
    analyze: (vdgId: string, outlierId?: string) => Promise<void>;
}

export function useSTPFFromVDG(): UseSTPFFromVDGReturn {
    const [data, setData] = useState<STPFAnalyzeResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const analyze = useCallback(async (vdgId: string, outlierId?: string) => {
        setLoading(true);
        setError(null);

        try {
            const result = await api.stpfAnalyzeVdg({
                vdg_id: vdgId,
                outlier_id: outlierId,
                apply_patches: true,
            });
            setData(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'VDG STPF 분석 실패');
            setData(null);
        } finally {
            setLoading(false);
        }
    }, []);

    return { data, loading, error, analyze };
}

// ==================
// useSTPFAutoAnalyze (with score prop)
// ==================

export function useSTPFAutoAnalyze(score: number | null) {
    const [grade, setGrade] = useState<STPFGradeResponse | null>(null);
    const [kelly, setKelly] = useState<STPFKellyResponse | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (score === null || score < 0) return;

        const fetchData = async () => {
            setLoading(true);
            try {
                const [gradeResult, kellyResult] = await Promise.all([
                    api.stpfGetGrade(score),
                    api.stpfKellyDecision(score),
                ]);
                setGrade(gradeResult);
                setKelly(kellyResult);
            } catch (err) {
                console.error('STPF auto analyze failed:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [score]);

    return { grade, kelly, loading };
}
