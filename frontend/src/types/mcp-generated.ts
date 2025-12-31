/**
 * MCP Generated Types
 * 자동 생성됨 - 직접 수정하지 마세요
 * Generated: 2025-12-31T23:00:26
 * Source: backend/app/mcp/schemas/
 */

// ==================
// Pattern Types
// ==================

/** 패턴 검색 결과 항목 */
export interface PatternResult {
    id?: string;
    title?: string;
    tier?: string | null;
    platform?: string | null;
    category?: string | null;
    score?: number | null;
    views?: number;
}

/** 검색 필터 */
export interface SearchFilters {
    category?: string | null;
    platform?: string | null;
    min_tier?: string;
    limit?: number;
}

/** 패턴 검색 응답 */
export interface SearchResponse {
    query?: string;
    filters?: SearchFilters;
    count?: number;
    results?: PatternResult[];
}

// ==================
// Pack Types
// ==================

/** VDG 분석 정보 */
export interface VDGInfo {
    quality_score?: number | null;
    quality_valid?: boolean | null;
    analysis_status?: string | null;
}

/** 소스팩 항목 */
export interface PackSource {
    id?: string;
    title?: string;
    platform?: string;
    category?: string;
    tier?: string | null;
    score?: number;
    views?: number;
    growth_rate?: number | null;
    video_url?: string;
    comments?: Record<string, any>[] | null;
    vdg?: VDGInfo | null;
}

/** 소스팩 생성 응답 */
export interface SourcePackResponse {
    name?: string;
    created_at?: string;
    outlier_count?: number;
    sources?: PackSource[];
}

// ==================
// Tool Result Types
// ==================

/** AI 분석 결과 */
export interface AIAnalysisResult {
    content: string;
    analysisType: "full" | "basic" | "vdg_only";
    outlierId: string;
    tier?: string;
    title?: string;
}

/** 배치 분석 결과 */
export interface BatchAnalysisResult {
    content: string;
    focus: "trends" | "comparison" | "strategy";
    outlierCount: number;
}

/** 성과 분석 결과 */
export interface PerformanceResult {
    content: string;
    period: "7d" | "30d" | "90d";
    outlierId: string;
}
