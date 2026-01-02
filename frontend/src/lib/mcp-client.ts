/**
 * MCP HTTP Client
 * Komission MCP 서버와 Streamable HTTP를 통한 통신
 * 
 * MCP 2025-11-25 스펙 준수
 * - Streamable HTTP Transport
 * - JSON-RPC 2.0 메시지 포맷
 */

const MCP_BASE_URL = process.env.NEXT_PUBLIC_MCP_URL || '/mcp';

// MCP JSON-RPC 요청 형식
interface MCPRequest {
    jsonrpc: '2.0';
    id: string | number;
    method: string;
    params?: Record<string, unknown>;
}

// MCP JSON-RPC 응답 형식
interface MCPResponse<T = unknown> {
    jsonrpc: '2.0';
    id: string | number;
    result?: T;
    error?: {
        code: number;
        message: string;
        data?: unknown;
    };
}

// 도구 호출 결과 타입
export interface ToolCallResult<T = unknown> {
    success: boolean;
    data?: T;
    error?: string;
}

// AI 분석 결과 타입
export interface AIAnalysisResult {
    content: string;
    analysisType: 'recommendation' | 'shooting_guide' | 'risk';
    outlierId: string;
    tier?: string;
    title?: string;
}

// 배치 분석 결과 타입
export interface BatchAnalysisResult {
    content: string;
    summaryFocus: 'trends' | 'comparison' | 'strategy';
    outlierCount: number;
}

// 패턴 검색 결과 타입
export interface PatternResult {
    id: string;
    title: string;
    tier?: string;
    platform?: string;
    category?: string;
    score?: number;
    views: number;
}

export interface SearchResponse {
    query: string;
    filters: {
        category?: string;
        platform?: string;
        min_tier: string;
        limit: number;
    };
    count: number;
    results: PatternResult[];
}

// 소스팩 소스 타입
export interface PackSource {
    id: string;
    title: string;
    platform: string;
    category: string;
    tier?: string;
    score: number;
    views: number;
    growth_rate?: string;
    video_url: string;
    comments?: Array<{ text: string; likes?: number }>;
    vdg?: {
        quality_score?: number;
        quality_valid?: boolean;
        analysis_status?: string;
    };
}

// 소스팩 생성 결과 타입
export interface SourcePackResult {
    name: string;
    created_at: string;
    outlier_count: number;
    sources: PackSource[];
    // markdown 형식일 경우 문자열로 반환
    markdown?: string;
}

/**
 * MCP HTTP Client
 * FastMCP 2.14+ Streamable HTTP 엔드포인트와 통신
 */
export class MCPClient {
    private requestId = 0;
    private baseUrl: string;

    constructor(baseUrl?: string) {
        this.baseUrl = baseUrl || MCP_BASE_URL;
    }

    /**
     * MCP JSON-RPC 요청 전송
     */
    private async sendRequest<T>(method: string, params?: Record<string, unknown>): Promise<MCPResponse<T>> {
        const request: MCPRequest = {
            jsonrpc: '2.0',
            id: ++this.requestId,
            method,
            params,
        };

        try {
            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`MCP request failed: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('[MCP] Request failed:', error);
            throw error;
        }
    }

    /**
     * MCP 도구 호출
     */
    async callTool<T = unknown>(toolName: string, args: Record<string, unknown> = {}): Promise<ToolCallResult<T>> {
        try {
            const response = await this.sendRequest<{ content: Array<{ text?: string; type: string }> }>(
                'tools/call',
                {
                    name: toolName,
                    arguments: args,
                }
            );

            if (response.error) {
                return {
                    success: false,
                    error: response.error.message,
                };
            }

            // MCP 도구 결과에서 텍스트 콘텐츠 추출
            const content = response.result?.content;
            if (content && content.length > 0) {
                const textContent = content.find(c => c.type === 'text');
                if (textContent?.text) {
                    // JSON 파싱 시도
                    try {
                        const parsed = JSON.parse(textContent.text);
                        return { success: true, data: parsed as T };
                    } catch {
                        // 텍스트 그대로 반환
                        return { success: true, data: textContent.text as unknown as T };
                    }
                }
            }

            return { success: true, data: response.result as unknown as T };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
            };
        }
    }

    /**
     * MCP 리소스 조회
     */
    async readResource(uri: string): Promise<ToolCallResult<string>> {
        try {
            const response = await this.sendRequest<{ contents: Array<{ text?: string; uri: string }> }>(
                'resources/read',
                { uri }
            );

            if (response.error) {
                return {
                    success: false,
                    error: response.error.message,
                };
            }

            const contents = response.result?.contents;
            if (contents && contents.length > 0) {
                return { success: true, data: contents[0].text };
            }

            return { success: false, error: 'No content returned' };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
            };
        }
    }

    // ========================================
    // 고수준 도구 메서드
    // ========================================

    /**
     * AI 패턴 분석 (LLM Sampling 사용)
     */
    async analyzePattern(
        outlierId: string,
        analysisType: 'recommendation' | 'shooting_guide' | 'risk' = 'recommendation'
    ): Promise<ToolCallResult<AIAnalysisResult>> {
        const result = await this.callTool<string>('smart_pattern_analysis', {
            outlier_id: outlierId,
            analysis_type: analysisType,
        });

        if (!result.success || !result.data) {
            return {
                success: false,
                error: result.error || 'Analysis failed',
            };
        }

        return {
            success: true,
            data: {
                content: result.data as string,
                analysisType,
                outlierId,
            },
        };
    }

    /**
     * AI 배치 트렌드 분석
     */
    async batchAnalysis(
        outlierIds: string[],
        focus: 'trends' | 'comparison' | 'strategy' = 'trends'
    ): Promise<ToolCallResult<BatchAnalysisResult>> {
        const result = await this.callTool<string>('ai_batch_analysis', {
            outlier_ids: outlierIds,
            focus: focus,  // Backend에서 summary_focus → focus로 변경됨
        });

        if (!result.success || !result.data) {
            return {
                success: false,
                error: result.error || 'Batch analysis failed',
            };
        }

        return {
            success: true,
            data: {
                content: result.data as string,
                summaryFocus: focus,
                outlierCount: outlierIds.length,
            },
        };
    }

    /**
     * 패턴 검색
     */
    async searchPatterns(
        query: string,
        options?: {
            category?: string;
            platform?: string;
            minTier?: string;
            limit?: number;
            outputFormat?: 'markdown' | 'json';
        }
    ): Promise<ToolCallResult<SearchResponse | string>> {
        return this.callTool('search_patterns', {
            query,
            category: options?.category,
            platform: options?.platform,
            min_tier: options?.minTier || 'C',
            limit: options?.limit || 10,
            output_format: options?.outputFormat || 'json',
        });
    }

    /**
     * 패턴 정보 조회 (리소스)
     */
    async getPattern(clusterId: string): Promise<ToolCallResult<string>> {
        return this.readResource(`komission://patterns/${clusterId}`);
    }

    /**
     * 아웃라이어 댓글 조회 (리소스)
     */
    async getComments(outlierId: string): Promise<ToolCallResult<string>> {
        return this.readResource(`komission://comments/${outlierId}`);
    }

    /**
     * VDG 분석 조회 (리소스)
     */
    async getVDG(outlierId: string): Promise<ToolCallResult<string>> {
        return this.readResource(`komission://vdg/${outlierId}`);
    }

    /**
     * Director Pack 조회 (리소스)
     */
    async getDirectorPack(outlierId: string): Promise<ToolCallResult<string>> {
        return this.readResource(`komission://director-pack/${outlierId}`);
    }

    // ========================================
    // Source Pack 도구
    // ========================================

    /**
     * 소스팩 생성 결과 타입
     */


    /**
     * NotebookLM 소스팩 생성
     * 
     * @param outlierIds - 포함할 아웃라이어 ID 목록
     * @param packName - 소스팩 이름
     * @param options - 추가 옵션 (include_comments, include_vdg, output_format)
     * @returns 소스팩 데이터 (markdown 또는 JSON)
     */
    async generateSourcePack(
        outlierIds: string[],
        packName: string,
        options: {
            includeComments?: boolean;
            includeVdg?: boolean;
            outputFormat?: 'markdown' | 'json';
        } = {}
    ): Promise<ToolCallResult<SourcePackResult>> {
        const {
            includeComments = true,
            includeVdg = true,
            outputFormat = 'markdown'
        } = options;

        return this.callTool<SourcePackResult>('generate_source_pack', {
            outlier_ids: outlierIds,
            pack_name: packName,
            include_comments: includeComments,
            include_vdg: includeVdg,
            output_format: outputFormat,
        });
    }

    /**
     * MCP 서버 상태 확인
     */
    async ping(): Promise<boolean> {
        try {
            const response = await this.sendRequest('ping');
            return !response.error;
        } catch {
            return false;
        }
    }
}

// 싱글톤 인스턴스
export const mcpClient = new MCPClient();
