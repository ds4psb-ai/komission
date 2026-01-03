/**
 * Komission API Client
 * Handles all backend API communication
 */

const API_BASE_URL = ''; // Use relative path to leverage Next.js proxy


interface ApiErrorPayload {
    detail?: string;
    message?: string;
}

/**
 * 보호된 페이지 목록 (401 시 로그인 리다이렉트)
 * 이 목록에 없는 페이지에서는 401이 발생해도 리다이렉트하지 않음
 */
const PROTECTED_PATHS = [
    '/my',           // 마이페이지
    '/ops',          // Ops Console (관리자)
    '/session',      // 촬영하기
    '/collabs/apply', // 체험단 신청
    '/calibration',  // 취향 캘리브레이션
    '/curation',     // 큐레이션 (로그인 필요)
];

/**
 * 현재 페이지가 보호된 페이지인지 확인
 */
function isProtectedPage(): boolean {
    if (typeof window === 'undefined') return false;
    const path = window.location.pathname;
    return PROTECTED_PATHS.some(p => path.startsWith(p));
}

export class ApiClient {
    private token: string | null = null;

    setToken(token: string) {
        this.token = token;
        if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', token);
        }
    }

    getToken(): string | null {
        if (this.token) return this.token;
        if (typeof window !== 'undefined') {
            return localStorage.getItem('access_token');
        }
        return null;
    }

    clearToken() {
        this.token = null;
        if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
        }
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const token = this.getToken();
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
            ...options.headers,
        };

        let response: Response;
        try {
            response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers,
            });
        } catch (error) {
            throw new Error('서버에 연결할 수 없습니다.');
        }

        const contentType = response.headers.get('content-type') || '';
        const isJson = contentType.includes('application/json');

        if (!response.ok) {
            // Handle token expiration (401 Unauthorized)
            if (response.status === 401) {
                console.warn('[API] Token expired or invalid, logging out...');
                this.clearToken();

                // 보호된 페이지에서만 리다이렉트 (PUBLIC 페이지에서는 에러만 표시)
                if (typeof window !== 'undefined') {
                    if (isProtectedPage() && !window.location.pathname.includes('/login')) {
                        window.location.href = '/login?expired=true';
                    }
                }
                throw new Error('세션이 만료되었습니다. 다시 로그인해 주세요.');
            }

            let detail = `${response.status} ${response.statusText}`;
            if (isJson) {
                const error: ApiErrorPayload | null = await response.json().catch(() => null);
                if (error?.detail) detail = error.detail;
                if (!error?.detail && error?.message) detail = error.message;
            } else {
                const text = await response.text().catch(() => '');
                if (text) detail = text.slice(0, 140);
            }

            throw new Error(detail || '오류가 발생했습니다.');
        }

        if (response.status === 204) {
            return null as T;
        }

        if (isJson) {
            return response.json();
        }

        const text = await response.text();
        return text as unknown as T;
    }

    private async safeRequest<T>(
        endpoint: string,
        options: RequestInit,
        fallback: T
    ): Promise<T> {
        try {
            return await this.request<T>(endpoint, options);
        } catch (error) {
            if (process.env.NODE_ENV !== 'production') {
                console.warn(`[API] ${endpoint} failed`, error);
            }
            return fallback;
        }
    }

    // Auth
    async login(email: string, password: string) {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_BASE_URL}/api/v1/auth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();
        this.setToken(data.access_token);
        return data; // Returns Token { access_token, token_type, expires_in }
    }

    // Google OAuth login
    async googleAuth(credential: string): Promise<AuthResponse> {
        // MOCK AUTH HANDLING
        if (
            process.env.NEXT_PUBLIC_MOCK_AUTH === 'true' &&
            credential === 'mock.credential.token'
        ) {
            console.log('Using Mock Auth Login...');
            // 1. Get Token via Dev Backdoor
            const tokenData = await this.login('admin@komission.ai', 'ignored'); // Password ignored in dev

            // 2. Get User Data
            this.setToken(tokenData.access_token);
            const user = await this.getMe();

            // 3. Construct AuthResponse
            return {
                access_token: tokenData.access_token,
                token_type: tokenData.token_type,
                expires_in: tokenData.expires_in,
                user: user
            };
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credential }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Google login failed' }));
            throw new Error(error.detail);
        }

        const data: AuthResponse = await response.json();
        this.setToken(data.access_token);
        return data;
    }

    async getMe(): Promise<User> {
        return this.request<User>('/api/v1/auth/me');
    }

    async logout() {
        await this.request('/api/v1/auth/logout', { method: 'POST' }).catch(() => { });
        this.clearToken();
    }

    // Remix Nodes
    async listRemixNodes(params?: { skip?: number; limit?: number; layer?: string }) {
        const query = new URLSearchParams();
        if (params?.skip) query.set('skip', params.skip.toString());
        if (params?.limit) query.set('limit', params.limit.toString());
        if (params?.layer) query.set('layer', params.layer);

        return this.request<RemixNode[]>(`/api/v1/remix?${query}`);
    }

    async getMyStats(): Promise<UserStats> {
        return this.request<UserStats>('/api/v1/remix/my/stats');
    }

    async getRemixNode(nodeId: string) {
        return this.request<RemixNodeDetail>(`/api/v1/remix/${nodeId}`);
    }

    async createRemixNode(data: CreateRemixNodeInput) {
        return this.request<RemixNode>('/api/v1/remix', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async forkRemixNode(
        nodeId: string,
        mutations?: Record<string, unknown>,
        deviceFingerprint?: string
    ) {
        // 🛡️ Generate simple fingerprint if not provided
        const fp = deviceFingerprint || this.generateSimpleFingerprint();

        return this.request<RemixNode>(`/api/v1/remix/${nodeId}/fork`, {
            method: 'POST',
            body: JSON.stringify({
                ...mutations,
                device_fingerprint: fp
            }),
        });
    }


    /**
     * Generate a simple browser fingerprint for anti-abuse.
     * Not as robust as FingerprintJS but works without external deps.
     */
    private generateSimpleFingerprint(): string {
        if (typeof window === 'undefined') return 'ssr';

        const components = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset(),
            navigator.hardwareConcurrency || 0,
        ];

        // Simple hash
        const str = components.join('|');
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0;
        }
        return 'fp_' + Math.abs(hash).toString(36);
    }

    async analyzeNode(nodeId: string) {
        return this.request<{ status: string; analysis: unknown }>(
            `/api/v1/remix/${nodeId}/analyze`,
            { method: 'POST' }
        );
    }

    // --- Mutation Strategy & Genealogy ---
    async getMutationStrategy(nodeId: string) {
        return this.request<MutationStrategyResponse[]>(`/api/v1/remix/mutation-strategy/${nodeId}`);
    }

    async getRemixNodeGenealogy(nodeId: string, depth = 3) {
        return this.request<GenealogyResponse>(`/api/v1/remix/genealogy/${nodeId}?depth=${depth}`);
    }

    // --- Feedback Loop ---
    async reportPerformance(data: { node_id: string; actual_retention: number; actual_views?: number; source?: string }) {
        return this.request<{ calibrated: boolean; details: unknown[] }>('/api/v1/remix/calibrate', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getPatternConfidence(patternCode: string, type = 'visual') {
        return this.request<PatternConfidenceResponse>(`/api/v1/remix/pattern-confidence/${patternCode}?pattern_type=${type}`);
    }

    async getPatternConfidenceRanking(minSamples = 5) {
        return this.request<PatternRankingResponse>(`/api/v1/remix/pattern-confidence-ranking?min_samples=${minSamples}`);
    }

    // --- GA/RL Optimization ---
    async optimizePattern(data: { category?: string; mood?: string; sequence_length?: number; generations?: number }) {
        return this.request<PatternOptimizationResponse>('/api/v1/remix/optimize-pattern', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getPatternSuggestions(category?: string) {
        let url = '/api/v1/remix/pattern-suggestions';
        if (category) url += `?category=${category}`;
        return this.request<PatternSuggestionResponse>(url);
    }

    // Quest Matching (Expert Recommendation)
    async getQuestMatching(nodeId: string, options?: {
        category?: string;
        music_genre?: string;
        platform?: string;
    }): Promise<QuestMatchingResponse> {
        return this.request<QuestMatchingResponse>(`/api/v1/remix/${nodeId}/matching`, {
            method: 'POST',
            body: JSON.stringify(options || {}),
        });
    }

    // Pipelines (Canvas Persistence)
    async listPublicPipelines() {
        return this.request<Pipeline[]>('/api/v1/pipelines/public');
    }

    async listPipelines() {
        return this.request<Pipeline[]>('/api/v1/pipelines/');
    }

    async savePipeline(data: PipelineCreate) {
        return this.request<Pipeline>('/api/v1/pipelines/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async loadPipeline(id: string) {
        return this.request<Pipeline>(`/api/v1/pipelines/${id}`);
    }

    async updatePipeline(id: string, data: Partial<PipelineCreate>) {
        return this.request<Pipeline>(`/api/v1/pipelines/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }


    // Royalty System
    async getMyRoyalty() {
        return this.request<RoyaltySummary>('/api/v1/royalty/my');
    }

    async getNodeEarnings(nodeId: string) {
        return this.request<NodeEarnings>(`/api/v1/royalty/node/${nodeId}/earnings`);
    }

    async getMyEarningNodes(skip = 0, limit = 20) {
        return this.request<EarningNode[]>(`/api/v1/royalty/my/nodes?skip=${skip}&limit=${limit}`);
    }

    async getCreatorLeaderboard(limit = 10) {
        return this.request<LeaderboardEntry[]>(`/api/v1/royalty/leaderboard?limit=${limit}`);
    }

    async getRoyaltyHistory(reason?: string, skip = 0, limit = 50) {
        let url = `/api/v1/royalty/history?skip=${skip}&limit=${limit}`;
        if (reason) {
            url += `&reason=${reason}`;
        }
        return this.request<RoyaltyTransaction[]>(url);
    }

    async getRoyaltyStats() {
        return this.request<RoyaltyStats>('/api/v1/royalty/stats');
    }

    // Gamification (Expert Recommendation)
    async getMyBadges(): Promise<Badge[]> {
        return this.request<Badge[]>('/api/v1/gamification/badges');
    }

    async getMyStreak(): Promise<StreakInfo> {
        return this.request<StreakInfo>('/api/v1/gamification/streak');
    }

    async checkInStreak(): Promise<StreakCheckInResponse> {
        return this.request<StreakCheckInResponse>('/api/v1/gamification/streak/check-in', {
            method: 'POST',
        });
    }

    async getDailyMissions(): Promise<DailyMission[]> {
        return this.request<DailyMission[]>('/api/v1/gamification/missions/daily');
    }

    async completeMission(missionType: string): Promise<MissionCompleteResponse> {
        return this.request<MissionCompleteResponse>(`/api/v1/gamification/missions/${missionType}/complete`, {
            method: 'POST',
        });
    }

    async getGamificationLeaderboard(limit: number = 10): Promise<GamificationLeaderboardEntry[]> {
        return this.request<GamificationLeaderboardEntry[]>(`/api/v1/gamification/leaderboard?limit=${limit}`);
    }

    // --- Phase 3: Taste Calibration ---
    async getCalibrationPairs(): Promise<CalibrationPairResponse> {
        return this.request<CalibrationPairResponse>('/api/v1/calibration/pairs');
    }

    async submitCalibrationChoice(
        pairId: string,
        selectedOptionId: string,
        selection: 'A' | 'B'
    ): Promise<CalibrationSubmitResponse> {
        // Authenticated user ID is extracted from token in backend, 
        // but for now we might need to pass it if the backend expects it in payload.
        // Assuming backend extracts from token, but payload requires creator_id.
        // Let's get user from getMe() or local storage if needed. 
        // For simplicity, we'll fetch me first or rely on token.
        // Re-reading backend schema: CalibrationSubmitRequest requires creator_id.

        const user = await this.getMe();
        return this.request<CalibrationSubmitResponse>('/api/v1/calibration/choice', {
            method: 'POST',
            body: JSON.stringify({
                creator_id: user.id,
                pair_id: pairId,
                selected_option_id: selectedOptionId,
                selection: selection
            })
        });
    }

    // --- Evidence Loop (Phase 4) ---
    async getEvidenceTable(nodeId: string, period = "4w", format: "json" | "csv" = "json") {
        if (format === "csv") {
            // For CSV, we need to handle the blob download
            const token = this.getToken();
            const response = await fetch(`${API_BASE_URL}/api/v1/remix/${nodeId}/evidence?period=${period}&format=csv`, {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            });
            if (!response.ok) throw new Error("Failed to download CSV");
            return response.blob();
        }
        return this.request<EvidenceTableResponse>(`/api/v1/remix/${nodeId}/evidence?period=${period}`);
    }

    async createEvidenceSnapshot(nodeId: string, period = "4w") {
        return this.request<EvidenceSnapshotResponse>(`/api/v1/remix/${nodeId}/evidence/snapshot?period=${period}`, {
            method: 'POST'
        });
    }

    async getVDGSummary(nodeId: string, period = "4w") {
        return this.request<VDGSummaryResponse>(`/api/v1/remix/${nodeId}/vdg-summary?period=${period}`);
    }

    // Health
    async health() {
        return this.request<{ status: string; version: string }>('/health');
    }

    // ==================
    // EVIDENCE BOARDS (Phase B)
    // ==================
    async listBoards(): Promise<EvidenceBoard[]> {
        return this.request<EvidenceBoard[]>('/api/v1/boards');
    }

    async createBoard(data: CreateBoardInput): Promise<EvidenceBoard> {
        return this.request<EvidenceBoard>('/api/v1/boards', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getBoard(boardId: string): Promise<EvidenceBoardDetail> {
        return this.request<EvidenceBoardDetail>(`/api/v1/boards/${boardId}`);
    }

    async addBoardItem(boardId: string, data: AddBoardItemInput): Promise<BoardItem> {
        return this.request<BoardItem>(`/api/v1/boards/${boardId}/items`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async setBoardConclusion(boardId: string, data: SetConclusionInput): Promise<EvidenceBoard> {
        return this.request<EvidenceBoard>(`/api/v1/boards/${boardId}/conclusion`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async removeBoardItem(boardId: string, itemId: string): Promise<void> {
        return this.request<void>(`/api/v1/boards/${boardId}/items/${itemId}`, {
            method: 'DELETE',
        });
    }

    // ==================
    // KNOWLEDGE CENTER (Phase C)
    // ==================
    async getHookLibrary(options?: { pattern_type?: string; min_samples?: number; limit?: number }): Promise<HookLibraryResponse> {
        const params = new URLSearchParams();
        if (options?.pattern_type) params.set('pattern_type', options.pattern_type);
        if (options?.min_samples) params.set('min_samples', options.min_samples.toString());
        if (options?.limit) params.set('limit', options.limit.toString());
        const query = params.toString();
        return this.request<HookLibraryResponse>(`/api/v1/knowledge/hooks${query ? '?' + query : ''}`);
    }

    async getHookDetail(patternCode: string): Promise<HookDetailResponse> {
        return this.request<HookDetailResponse>(`/api/v1/knowledge/hooks/${patternCode}`);
    }

    async getEvidenceGuides(options?: { category?: string; platform?: string; min_confidence?: number }): Promise<EvidenceGuideResponse> {
        const params = new URLSearchParams();
        if (options?.category) params.set('category', options.category);
        if (options?.platform) params.set('platform', options.platform);
        if (options?.min_confidence) params.set('min_confidence', options.min_confidence.toString());
        const query = params.toString();
        return this.request<EvidenceGuideResponse>(`/api/v1/knowledge/guides${query ? '?' + query : ''}`);
    }

    async getEvidenceGuideDetail(snapshotId: string): Promise<EvidenceGuideDetail> {
        return this.request<EvidenceGuideDetail>(`/api/v1/knowledge/guides/${snapshotId}`);
    }

    // ==================
    // CRAWLERS (Automation API)
    // ==================
    async runCrawler(data: RunCrawlerInput): Promise<CrawlerJobResponse> {
        return this.request<CrawlerJobResponse>('/api/v1/crawlers/run', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getCrawlerJob(jobId: string): Promise<CrawlerJobStatus> {
        return this.request<CrawlerJobStatus>(`/api/v1/crawlers/jobs/${jobId}`);
    }

    async getCrawlerStatus(): Promise<CrawlerStatusResponse> {
        return this.request<CrawlerStatusResponse>('/api/v1/crawlers/status');
    }

    async getCrawlerHealth(): Promise<CrawlerHealthResponse> {
        return this.request<CrawlerHealthResponse>('/api/v1/crawlers/health');
    }

    // ==================
    // OUTLIERS (VDG Analysis Gate)
    // ==================
    async listOutliers(options?: {
        category?: string;
        platform?: string;
        tier?: string;
        status?: string;
        freshness?: string;
        sortBy?: string;
        limit?: number;
    }): Promise<OutlierListResponse> {
        const params = new URLSearchParams();
        if (options?.category) params.set('category', options.category);
        if (options?.platform) params.set('platform', options.platform);
        if (options?.tier) params.set('tier', options.tier);
        if (options?.status) params.set('status', options.status);
        if (options?.freshness) params.set('freshness', options.freshness);
        if (options?.sortBy) params.set('sort_by', options.sortBy);
        if (options?.limit) params.set('limit', options.limit.toString());
        const query = params.toString();
        return this.request<OutlierListResponse>(`/api/v1/outliers${query ? '?' + query : ''}`);
    }

    async promoteOutlier(itemId: string, campaignEligible: boolean = false): Promise<PromoteOutlierResponse> {
        return this.request<PromoteOutlierResponse>(`/api/v1/outliers/items/${itemId}/promote`, {
            method: 'POST',
            body: JSON.stringify({ campaign_eligible: campaignEligible }),
        });
    }

    async approveVDGAnalysis(itemId: string): Promise<ApproveVDGResponse> {
        return this.request<ApproveVDGResponse>(`/api/v1/outliers/items/${itemId}/approve`, {
            method: 'POST',
        });
    }

    async rejectOutlier(itemId: string, reason?: string, notes?: string): Promise<{ rejected: boolean; item_id: string }> {
        return this.request<{ rejected: boolean; item_id: string }>(`/api/v1/outliers/items/${itemId}/reject`, {
            method: 'POST',
            body: JSON.stringify({ reason, notes }),
        });
    }


    async createOutlierManual(data: {
        video_url: string;
        platform: string;
        category: string;
        title?: string;
        thumbnail_url?: string;
    }): Promise<OutlierItem> {
        return this.request<OutlierItem>('/api/v1/outliers/items/manual', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // ==================
    // PATTERN LIBRARY (PEGL v1.0)
    // ==================
    async getPatternLibrary(options?: { cluster_id?: string; platform?: string; limit?: number }): Promise<PatternLibraryResponse> {
        const params = new URLSearchParams();
        if (options?.cluster_id) params.set('cluster_id', options.cluster_id);
        if (options?.platform) params.set('platform', options.platform);
        if (options?.limit) params.set('limit', options.limit.toString());
        const query = params.toString();
        return this.request<PatternLibraryResponse>(`/api/v1/patterns/library${query ? '?' + query : ''}`);
    }

    async getPatternDetail(patternId: string): Promise<PatternLibraryItem> {
        return this.request<PatternLibraryItem>(`/api/v1/patterns/library/${patternId}`);
    }

    // ==================
    // SOURCE PACKS (Phase D - NotebookLM Integration)
    // ==================
    async getSourcePacks(options?: { cluster_id?: string; has_notebook?: boolean; limit?: number }): Promise<SourcePackListResponse> {
        const params = new URLSearchParams();
        if (options?.cluster_id) params.set('cluster_id', options.cluster_id);
        if (options?.has_notebook !== undefined) params.set('has_notebook', options.has_notebook.toString());
        if (options?.limit) params.set('limit', options.limit.toString());
        const query = params.toString();
        return this.request<SourcePackListResponse>(`/api/v1/notebook-library/source-packs${query ? '?' + query : ''}`);
    }

    async getSourcePackDetail(packId: string): Promise<SourcePackDetail> {
        return this.request<SourcePackDetail>(`/api/v1/notebook-library/source-packs/${packId}`);
    }

    async uploadSourcePackToNotebook(packId: string): Promise<UploadToNotebookResponse> {
        return this.request<UploadToNotebookResponse>('/api/v1/notebook-library/source-packs/upload-to-notebook', {
            method: 'POST',
            body: JSON.stringify({ pack_id: packId }),
        });
    }

    // ==================
    // CREATOR FEEDBACK LOOP (P2)
    // ==================

    async submitCreatorVideo(data: {
        pattern_id: string;
        video_url: string;
        platform: 'tiktok' | 'instagram' | 'youtube';
        creator_notes?: string;
        invariant_checklist?: Record<string, boolean>;
    }): Promise<CreatorSubmissionResponse> {
        return this.request<CreatorSubmissionResponse>('/api/v1/creator/submissions', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getMySubmissions(limit = 20): Promise<CreatorSubmissionListResponse> {
        return this.request<CreatorSubmissionListResponse>(`/api/v1/creator/submissions?limit=${limit}`);
    }

    async getSubmissionDetail(submissionId: string): Promise<CreatorSubmissionItem> {
        return this.request<CreatorSubmissionItem>(`/api/v1/creator/submissions/${submissionId}`);
    }

    // ==================
    // TEMPLATE SEEDS (Opal)
    // ==================
    async generateTemplateSeed(data: {
        parent_id?: string;
        cluster_id?: string;
        template_type?: 'capsule' | 'guide' | 'edit';
        context?: Record<string, unknown>;
    }): Promise<GenerateTemplateSeedResponse> {
        return this.request<GenerateTemplateSeedResponse>('/api/v1/template-seeds/generate', {
            method: 'POST',
            body: JSON.stringify({
                parent_id: data.parent_id || null,
                cluster_id: data.cluster_id || null,
                template_type: data.template_type || 'capsule',
                context: data.context || {},
            }),
        });
    }

    async getTemplateSeed(seedId: string): Promise<TemplateSeedDetail> {
        return this.request<TemplateSeedDetail>(`/api/v1/template-seeds/${seedId}`);
    }

    // ==================
    // P1: COACHING SESSION EVENTS
    // ==================

    /**
     * Create a new coaching session with control group assignment
     */
    async createCoachingSession(data: CreateCoachingSessionInput): Promise<CoachingSessionResponse> {
        return this.request<CoachingSessionResponse>('/api/v1/coaching/sessions', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * Log rule evaluation event (CRITICAL: log even without intervention)
     */
    async logRuleEvaluated(sessionId: string, data: LogRuleEvaluatedInput): Promise<LogEventResponse> {
        return this.request<LogEventResponse>(`/api/v1/coaching/sessions/${sessionId}/events/rule-evaluated`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * Log coaching intervention event
     */
    async logIntervention(sessionId: string, data: LogInterventionInput): Promise<LogEventResponse> {
        return this.request<LogEventResponse>(`/api/v1/coaching/sessions/${sessionId}/events/intervention`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * Log outcome event with automatic negative evidence detection
     */
    async logOutcome(sessionId: string, data: LogOutcomeInput): Promise<LogOutcomeResponse> {
        return this.request<LogOutcomeResponse>(`/api/v1/coaching/sessions/${sessionId}/events/outcome`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * Get all events for a session
     */
    async getSessionEvents(sessionId: string): Promise<SessionEventsResponse> {
        return this.request<SessionEventsResponse>(`/api/v1/coaching/sessions/${sessionId}/events`);
    }

    /**
     * Get session summary with quality metrics
     */
    async getSessionSummary(sessionId: string): Promise<SessionSummaryResponse> {
        return this.request<SessionSummaryResponse>(`/api/v1/coaching/sessions/${sessionId}/summary`);
    }

    /**
     * Get all sessions stats (for verifying control ratio)
     */
    async getAllSessionsStats(): Promise<AllSessionsStatsResponse> {
        return this.request<AllSessionsStatsResponse>('/api/v1/coaching/stats/all-sessions');
    }

    // ==================
    // STPF v3.1 (Single Truth Pattern Formalization)
    // ==================

    /**
     * STPF 빠른 점수 계산 (핵심 변수만)
     */
    async stpfQuickScore(data: {
        essence: number;
        novelty: number;
        proof: number;
        risk: number;
        network: number;
    }): Promise<STPFQuickScoreResponse> {
        return this.request<STPFQuickScoreResponse>('/api/v1/stpf/quick-score', {
            method: 'POST',
            body: JSON.stringify({
                gates: { trust_gate: 7, legality_gate: 8, hygiene_gate: 7 },
                numerator: {
                    essence: data.essence,
                    capability: 5,
                    novelty: data.novelty,
                    connection: 5,
                    proof: data.proof,
                },
                denominator: {
                    cost: 4,
                    risk: data.risk,
                    threat: 5,
                    pressure: 5,
                    time_lag: 4,
                    uncertainty: 5,
                },
                multipliers: {
                    scarcity: 5,
                    network: data.network,
                    leverage: 5,
                },
            }),
        });
    }

    /**
     * STPF 전체 분석
     */
    async stpfAnalyze(data: {
        gates: STPFGates;
        numerator: STPFNumerator;
        denominator: STPFDenominator;
        multipliers: STPFMultipliers;
        apply_patches?: boolean;
        update_bayesian?: boolean;
    }): Promise<STPFAnalyzeResponse> {
        return this.request<STPFAnalyzeResponse>('/api/v1/stpf/analyze/manual', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * VDG ID로 STPF 분석
     */
    async stpfAnalyzeVdg(data: {
        vdg_id: string;
        outlier_id?: string;
        apply_patches?: boolean;
    }): Promise<STPFAnalyzeResponse> {
        return this.request<STPFAnalyzeResponse>('/api/v1/stpf/analyze/vdg', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * STPF 등급 조회
     */
    async stpfGetGrade(score: number): Promise<STPFGradeResponse> {
        return this.request<STPFGradeResponse>(`/api/v1/stpf/grade/${score}`);
    }

    /**
     * Kelly Criterion 의사결정
     */
    async stpfKellyDecision(
        score: number,
        timeInvestmentHours: number = 10,
        expectedViewMultiplier: number = 3
    ): Promise<STPFKellyResponse> {
        const params = new URLSearchParams({
            time_investment_hours: timeInvestmentHours.toString(),
            expected_view_multiplier: expectedViewMultiplier.toString(),
        });
        return this.request<STPFKellyResponse>(`/api/v1/stpf/kelly/${score}?${params}`);
    }

    /**
     * ToT 시뮬레이션 (Worst/Base/Best)
     */
    async stpfSimulateTot(data: {
        gates: STPFGates;
        numerator: STPFNumerator;
        denominator: STPFDenominator;
        multipliers: STPFMultipliers;
        variation?: number;
    }): Promise<STPFToTResponse> {
        return this.request<STPFToTResponse>('/api/v1/stpf/simulate/tot', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * Monte Carlo 시뮬레이션
     */
    async stpfSimulateMonteCarlo(data: {
        gates: STPFGates;
        numerator: STPFNumerator;
        denominator: STPFDenominator;
        multipliers: STPFMultipliers;
        n_simulations?: number;
        noise_std?: number;
    }): Promise<STPFMonteCarloResponse> {
        return this.request<STPFMonteCarloResponse>('/api/v1/stpf/simulate/monte-carlo', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * STPF 변수 목록 조회
     */
    async stpfGetVariables(): Promise<{ gates: STPFGates; numerator: STPFNumerator; denominator: STPFDenominator; multipliers: STPFMultipliers }> {
        return this.request('/api/v1/stpf/variables');
    }

    /**
     * STPF 서비스 상태 확인
     */
    async stpfHealth(): Promise<{ status: string; version: Record<string, string>; endpoints: string[] }> {
        return this.request('/api/v1/stpf/health');
    }
}

// Evidence Loop Types
export interface EvidenceTableResponse {
    parent_node_id: string;
    generated_at: string;
    period: string;
    rows: Array<{
        parent_node_id: string;
        mutation_type: string;
        before_pattern: string;
        after_pattern: string;
        success_rate: number;
        sample_count: number;
        avg_delta: string;
        period: string;
        depth: number;
        confidence: number;
        risk: string;
        updated_at: string;
    }>;
    total_samples: number;
    top_recommendation: string | null;
}

export interface EvidenceSnapshotResponse {
    snapshot_id: string;
    parent_node_id: string;
    period: string;
    sample_count: number;
    top_mutation: string | null;
    created_at: string;
}

export interface VDGSummaryResponse {
    node_id: string;
    period: string;
    depth1: Record<string, Record<string, {
        success_rate: number;
        sample_count: number;
        avg_delta: string;
        confidence: number;
    }>>;
    depth2: Record<string, any> | null;
    sample_count: number;
    top_mutation: {
        type: string;
        pattern: string;
        rate: string;
        confidence: number;
    } | null;
}

export interface O2OLocation {
    id: string;
    location_id: string;
    place_name: string;
    address: string;
    lat: number;
    lng: number;
    campaign_type: string;
    campaign_title: string;
    brand: string | null;
    reward_points: number;
    reward_product?: string;
    active_end: string;
    category?: string | null; // Added for matching
}

export interface LeaderboardEntry {
    rank: number;
    user_id: string;
    user_name: string | null;
    total_royalty: number;
    node_count: number;
}


export interface O2OCampaign {
    id: string;
    campaign_type: string;
    campaign_title: string;
    brand: string | null;
    category: string | null;
    reward_points: number;
    reward_product: string | null;
    description: string | null;
    fulfillment_steps: string[] | null;
    place_name: string | null;
    address: string | null;
    active_start: string;
    active_end: string;
    max_participants: number | null;
}

export interface O2OApplication {
    id: string;
    campaign_id: string;
    campaign_title: string;
    campaign_type: string;
    status: string;
    created_at: string;
}

export interface User {
    id: string;
    email: string;
    name: string | null;
    role: string;
    k_points: number;
    profile_image: string | null;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
    user: User;
}

export interface GenealogyResponse {
    root: string;
    total_nodes: number;
    edges: Array<{
        parent: string;
        child: string;
        delta: string;
    }>;
    error?: string;
}

export interface MutationStrategyResponse {
    mutation_strategy: Record<string, any>;
    expected_boost: string;
    reference_views?: number;
    confidence: number;
    rationale: string;
}

export interface PatternConfidenceResponse {
    pattern_code: string;
    confidence_score: number;
    sample_count: number;
    avg_error: number | null;
    status: string;
}

export interface PatternRankingResponse {
    total_patterns: number;
    ranking: Array<{
        pattern_code: string;
        pattern_type: string;
        confidence: number;
        samples: number;
        avg_error: number;
    }>;
}

export interface PatternOptimizationResponse {
    best_sequence: Record<string, any>;
    best_fitness: number;
    generations: number;
    initial_fitness: number;
    improvement: number;
    history: number[];
    recommendation: string;
}

export interface PatternSuggestionResponse {
    category: string | null;
    suggestions: Array<{
        pattern: string;
        type: string;
        confidence: number;
        samples: number;
    }>;
    source: string;
}

export interface UserStats {
    total_views: number;
    total_forks: number;
    node_count: number;
    k_points: number;
    total_royalty_received: number;
    pending_royalty: number;
}

export interface RemixNode {
    id: string;
    node_id: string;
    title: string;
    layer: 'master' | 'fork' | 'fork_of_fork';
    permission: string;
    governed_by: string;
    genealogy_depth: number;
    source_video_url: string | null;
    platform: string | null;
    is_published: boolean;
    view_count: number;
    performance_delta: string | null;
    created_at: string;
}

export interface RemixNodeDetail extends RemixNode {
    gemini_analysis: Record<string, unknown> | null;
    claude_brief: Record<string, unknown> | null;
    storyboard_images: Record<string, string> | null;
    audio_guide_path: string | null;
    mutation_profile: Record<string, unknown> | null;
    performance_delta: string | null;
}

export interface CreateRemixNodeInput {
    title: string;
    source_video_url: string;
    platform?: string;
}

export interface Pipeline {
    id: string;
    title: string;
    graph_data: { nodes: unknown[]; edges: unknown[] };
    is_public: boolean;
    created_at: string;
    updated_at: string;
}

export interface PipelineCreate {
    title: string;
    graph_data: { nodes: unknown[]; edges: unknown[] };
    is_public?: boolean;
}

// Royalty System Types
export interface RoyaltySummary {
    user_id: string;
    total_earned: number;
    pending: number;
    k_points: number;
    recent_transactions: RoyaltyTransaction[];
}

export interface NodeEarnings {
    node_id: string;
    title: string;
    total_fork_count: number;
    total_royalty_earned: number;
    view_count: number;
    transactions: RoyaltyTransaction[];
}

export interface EarningNode {
    node_id: string;
    title: string;
    total_fork_count: number;
    total_royalty_earned: number;
    view_count: number;
    is_published: boolean;
    layer: string;
    created_at: string;
}

export interface LeaderboardEntry {
    rank: number;
    user_id: string;
    user_name: string | null;
    total_royalty: number;
    node_count: number;
}

export interface RoyaltyTransaction {
    id: string;
    points_earned: number;
    reason: 'fork' | 'view_milestone' | 'k_success' | 'genealogy_bonus';
    source_node_id: string;
    forked_node_id: string | null;
    forker_id: string | null;
    is_settled?: boolean;
    created_at: string;
}

export interface RoyaltyStats {
    total_distributed: number;
    total_transactions: number;
    breakdown_by_reason: Record<string, { count: number; total_points: number }>;
    top_earning_nodes: { node_id: string; title: string; royalty: number }[];
}

// Quest Matching Types (Expert Recommendation)
export interface QuestRecommendation {
    id: string;
    brand: string | null;
    campaign_title: string;
    category: string | null;
    reward_points: number;
    reward_product: string | null;
    place_name?: string | null;
    address?: string | null;
    deadline: string;
    campaign_type?: string | null;
    fulfillment_steps?: string[] | null;
}

export interface QuestMatchingResponse {
    node_id: string;
    inferred_category: string | null;
    recommended_quests: QuestRecommendation[];
    total_count: number;
}

// Gamification Types (Expert Recommendation)
export interface Badge {
    badge_type: string;
    emoji: string;
    name: string;
    description: string;
    earned_at: string;
}

export interface StreakInfo {
    current_streak: number;
    longest_streak: number;
    last_activity_date: string | null;
    streak_points_earned: number;
    next_milestone: number;
}

export interface StreakCheckInResponse {
    status: string;
    current_streak: number;
    longest_streak?: number;
    points_earned: number;
    new_badges: string[];
}

export interface DailyMission {
    mission_type: string;
    name: string;
    description: string;
    points: number;
    completed: boolean;
    reward_claimed: boolean;
}

export interface MissionCompleteResponse {
    status: string;
    points_awarded: number;
    total_points: number;
    message: string;
}

export interface GamificationLeaderboardEntry {
    rank: number;
    user_id: string;
    user_name: string;
    profile_image: string | null;
    total_points: number;
    total_royalty: number; // Alias for compatibility
    badge_count: number;
    current_streak: number;
    streak_days?: number; // Alias for backward compatibility
}

// Calibration Types
export interface CalibrationOption {
    id: string;
    label: string;
    description: string;
    icon?: string;
}

export interface CalibrationPair {
    pair_id: string;
    question: string;
    option_a: CalibrationOption;
    option_b: CalibrationOption;
}

export interface CalibrationPairResponse {
    session_id: string;
    pairs: CalibrationPair[];
}

export interface CalibrationSubmitResponse {
    status: string;
    saved_choice_id: string;
}

// ==================
// EVIDENCE BOARDS TYPES
// ==================
export interface EvidenceBoard {
    id: string;
    title: string;
    description: string | null;
    owner_id: string;
    kpi_target: string | null;
    conclusion: string | null;
    winner_item_id: string | null;
    status: 'DRAFT' | 'ACTIVE' | 'CONCLUDED';
    created_at: string;
    updated_at: string;
    concluded_at: string | null;
}

export interface BoardItem {
    id: string;
    board_id: string;
    outlier_item_id: string | null;
    remix_node_id: string | null;
    notes: string | null;
    added_at: string;
    item_data?: {
        title?: string;
        platform?: string;
        source_url?: string;
    };
}

export interface EvidenceBoardDetail extends EvidenceBoard {
    items: BoardItem[];
    item_count: number;
}

export interface CreateBoardInput {
    title: string;
    description?: string;
    kpi_target?: string;
}

export interface AddBoardItemInput {
    outlier_item_id?: string;
    remix_node_id?: string;
    notes?: string;
}

export interface SetConclusionInput {
    conclusion: string;
    winner_item_id?: string;
}

// ==================
// KNOWLEDGE CENTER TYPES
// ==================
export interface HookPattern {
    pattern_code: string;
    pattern_type: string;
    confidence_score: number;
    sample_count: number;
    avg_retention: number | null;
    description: string | null;
}

export interface HookLibraryResponse {
    total_patterns: number;
    top_hooks: HookPattern[];
    categories: string[];
    last_updated: string;
}

export interface HookDetailResponse {
    pattern_code: string;
    pattern_type: string;
    confidence_score: number;
    sample_count: number;
    avg_absolute_error: number | null;
    description: string | null;
    usage_tips: string[];
    examples: { source_url: string; category: string }[];
}

export interface EvidenceGuide {
    id: string;
    parent_title: string;
    platform: string;
    category: string;
    top_mutation_type: string | null;
    top_mutation_pattern: string | null;
    success_rate: string | null;
    recommendation: string;
    sample_count: number;
    confidence: number;
}

export interface EvidenceGuideResponse {
    total_guides: number;
    guides: EvidenceGuide[];
}

export interface EvidenceGuideDetail {
    id: string;
    parent_node: {
        id: string;
        node_id: string;
        title: string;
        platform: string | null;
        source_video_url: string | null;
    };
    snapshot_date: string;
    period: string;
    depth1_summary: Record<string, unknown> | null;
    depth2_summary: Record<string, unknown> | null;
    top_mutation: {
        type: string | null;
        pattern: string | null;
        rate: string | null;
    };
    sample_count: number;
    confidence: number;
    recommendation: string;
    execution_steps: string[];
}

// ==================
// CRAWLER TYPES
// ==================
export interface RunCrawlerInput {
    platforms: string[];
    limit?: number;
    category?: string;
    region?: string;
}

export interface CrawlerJobResponse {
    job_id: string;
    status: string;
    platforms: string[];
    created_at: string;
}

export interface CrawlerJobStatus {
    job_id: string;
    status: 'running' | 'completed' | 'failed';
    platforms: string[];
    results: Record<string, { collected?: number; inserted?: number; error?: string }>;
    created_at: string;
    completed_at: string | null;
}

export interface CrawlerStatusResponse {
    platforms: {
        youtube: { count: number; last_crawl: string | null };
        tiktok: { count: number; last_crawl: string | null };
        instagram: { count: number; last_crawl: string | null };
    };
    running_jobs: number;
}

export interface CrawlerHealthResponse {
    status: string;
    platforms: Record<string, {
        status: string;
        last_crawl: string | null;
        item_count: number;
        is_stale: boolean;
    }>;
    running_jobs: number;
    quotas?: Record<string, { used: number; limit: number; remaining: number }>;
}

// ==================
// OUTLIER TYPES (VDG Analysis Gate)
// ==================

// VDG Analysis sub-types (from raw_payload.vdg_analysis)
export interface VDGDopamineRadar {
    visual_spectacle?: number;
    audio_stimulation?: number;
    narrative_intrigue?: number;
    emotional_resonance?: number;
    comedy_shock?: number;
}

export interface VDGIronyAnalysis {
    setup?: string;
    twist?: string;
    gap_type?: string;
}

export interface VDGMicrobeats {
    start?: string;
    build?: string;
    punch?: string;
}

export interface VDGHookGenome {
    pattern?: string;
    delivery?: string;
    strength?: number;
    hook_summary?: string;
    microbeats?: VDGMicrobeats;
    virality_analysis?: Record<string, string>;
}

export interface VDGIntentLayer {
    hook_trigger?: string;
    hook_trigger_reason?: string;
    retention_strategy?: string;
    dopamine_radar?: VDGDopamineRadar;
    irony_analysis?: VDGIronyAnalysis;
}

export interface VDGProductionConstraints {
    min_actors?: number;
    locations?: string[];
    props?: string[];
    difficulty?: string;
    primary_challenge?: string;
}

export interface VDGCapsuleBrief {
    hook_script?: string;
    constraints?: VDGProductionConstraints;
    do_not?: string[];
}

export interface VDGAnalysis {
    title?: string;
    hook_genome?: VDGHookGenome;
    intent_layer?: VDGIntentLayer;
    capsule_brief?: VDGCapsuleBrief;
    scenes?: Array<Record<string, unknown>>;
}

export interface OutlierItem {
    id: string;
    external_id: string;
    video_url: string;
    platform: string;
    category: string;
    title: string | null;
    thumbnail_url: string | null;
    view_count: number;
    like_count: number;
    share_count: number;
    outlier_score: number;
    outlier_tier: string;
    creator_avg_views: number;
    creator_username?: string | null;
    upload_date?: string | null;  // Original video upload date from platform
    engagement_rate: number;
    crawled_at: string | null;
    status: 'pending' | 'selected' | 'rejected' | 'promoted';
    // VDG Analysis Gate
    analysis_status: 'pending' | 'approved' | 'analyzing' | 'completed' | 'skipped' | 'comments_pending_review' | 'comments_failed' | 'comments_ready';
    promoted_to_node_id: string | null;
    best_comments_count: number;
    // VDG Analysis Data (from raw_payload)
    vdg_analysis?: VDGAnalysis | null;
}

export interface OutlierListResponse {
    total: number;
    items: OutlierItem[];
}

export interface PromoteOutlierResponse {
    promoted: boolean;
    item_id: string;
    node_id: string;
    remix_id: string;
    analysis_status: string;
    message: string;
}

export interface ApproveVDGResponse {
    approved: boolean;
    item_id: string;
    node_id: string;
    analysis_status: string;
    approved_by: string;
    message: string;
}

// ==================
// PATTERN LIBRARY TYPES (PEGL v1.0)
// ==================
export interface PatternLibraryItem {
    id: string;
    pattern_id: string;
    cluster_id: string;
    temporal_phase: string;
    platform: string;
    category: string;
    invariant_rules: Record<string, any>;
    mutation_strategy: Record<string, any>;
    citations: any[] | null;
    revision: number;
    created_at: string;
}

export interface PatternLibraryResponse {
    total: number;
    patterns: PatternLibraryItem[];
}

// ==================
// SOURCE PACK TYPES (Phase D)
// ==================
export interface SourcePackItem {
    id: string;
    cluster_id: string;
    temporal_phase: string;
    pack_type: string;
    drive_url: string | null;
    notebook_id: string | null;
    output_targets: string | null;
    pack_mode: string | null;
    entry_count: number;
    created_at: string;
}

export interface SourcePackListResponse {
    total: number;
    source_packs: SourcePackItem[];
}

export interface SourcePackDetail extends SourcePackItem {
    drive_file_id: string;
    schema_version: string | null;
    inputs_hash: string | null;
}

export interface UploadToNotebookResponse {
    success: boolean;
    notebook_id: string | null;
    message: string;
}

// ==================
// CREATOR SUBMISSION TYPES (P2 Feedback Loop)
// ==================
export interface CreatorSubmissionResponse {
    id: string;
    pattern_id: string;
    video_url: string;
    platform: string;
    status: string;
    submitted_at: string;
    message: string;
}

export interface CreatorSubmissionItem {
    id: string;
    pattern_id: string;
    video_url: string;
    platform: string;
    status: string;
    submitted_at: string;
    final_view_count: number | null;
    performance_vs_baseline: string | null;
}

export interface CreatorSubmissionListResponse {
    total: number;
    submissions: CreatorSubmissionItem[];
}

// ==================
// TEMPLATE SEEDS (Opal)
// ==================
export interface TemplateSeedParams {
    hook?: string;
    shotlist?: string[];
    audio?: string;
    scene?: string;
    timing?: string[];
    do_not?: string[];
}

export interface TemplateSeedDetail {
    seed_id: string;
    parent_id: string | null;
    cluster_id: string | null;
    template_type: 'capsule' | 'guide' | 'edit';
    prompt_version: string;
    seed_params: TemplateSeedParams;
    created_at: string;
}

export interface GenerateTemplateSeedResponse {
    success: boolean;
    seed?: TemplateSeedDetail;
    error?: string;
}

// ==================
// P1: COACHING SESSION TYPES
// ==================

export interface CreateCoachingSessionInput {
    director_pack?: any;  // Optional: Complete DirectorPack JSON
    video_id?: string;    // Or: Just video ID for server-side loading
    language?: string;
    voice_style?: 'strict' | 'friendly' | 'neutral';
}

export interface CoachingSessionResponse {
    session_id: string;
    status: 'created' | 'active' | 'ended' | 'error';
    websocket_url: string;
    created_at: string;
    expires_at: string;
    pattern_id: string;
    goal?: string;
    assignment: 'coached' | 'control';
    holdout_group: boolean;
}

export interface LogRuleEvaluatedInput {
    rule_id: string;
    ap_id: string;
    checkpoint_id: string;
    result: 'passed' | 'violated' | 'unknown';
    result_reason?: string;
    t_video: number;
    metric_id?: string;
    metric_value?: number;
    evidence_id?: string;
    intervention_triggered: boolean;
}

export interface LogInterventionInput {
    intervention_id: string;
    rule_id: string;
    ap_id?: string;
    checkpoint_id: string;
    t_video: number;
    command_text?: string;
    evidence_id?: string;
}

export interface LogOutcomeInput {
    intervention_id: string;
    compliance_detected: boolean;
    compliance_unknown_reason?: string;
    user_response?: string;
    metric_id?: string;
    metric_before?: number;
    metric_after?: number;
    upload_outcome_proxy?: string;
    reported_views?: number;
    reported_likes?: number;
    reported_saves?: number;
    outcome_unknown_reason?: string;
}

export interface LogEventResponse {
    logged: boolean;
    event_id: string;
}

export interface LogOutcomeResponse extends LogEventResponse {
    is_negative_evidence: boolean;
    negative_reason?: string;
}

export interface SessionEventsResponse {
    session_id: string;
    total_events: number;
    events: any[];  // SessionEvent[]
}

export interface SessionSummaryResponse {
    session_id: string;
    pack_id: string;
    assignment: string;
    holdout_group: boolean;
    total_events: number;
    rules_evaluated: number;
    interventions_delivered: number;
    outcomes_observed: number;
    intervention_outcome_join_rate: number;
    compliance_unknown_rate: number;
    negative_evidence_rate: number;
}

export interface AllSessionsStatsResponse {
    total_sessions: number;
    control_sessions: number;
    control_ratio: number;
    holdout_sessions: number;
    avg_intervention_outcome_join_rate: number;
    avg_compliance_unknown_rate: number;
}

// ==================
// STPF v3.1 Types
// ==================

export interface STPFGates {
    trust_gate: number;
    legality_gate: number;
    hygiene_gate: number;
}

export interface STPFNumerator {
    essence: number;
    capability: number;
    novelty: number;
    connection: number;
    proof: number;
}

export interface STPFDenominator {
    cost: number;
    risk: number;
    threat: number;
    pressure: number;
    time_lag: number;
    uncertainty: number;
}

export interface STPFMultipliers {
    scarcity: number;
    network: number;
    leverage: number;
}

export interface STPFResult {
    raw_score: number;
    score_1000: number;
    go_nogo: 'GO' | 'CONSIDER' | 'NO-GO';
    gate_passed: boolean;
    why?: string;
    how?: string[];
    improvements?: string[];
}

export interface STPFAnalyzeResponse {
    success: boolean;
    result?: STPFResult;
    mapping_info: Record<string, any>;
    validation_info: Record<string, any>;
    metadata: Record<string, any>;
    bayesian_info: Record<string, any>;
    patch_info: Record<string, any>;
    anchor_interpretations: Record<string, any>;
    error?: string;
}

export interface STPFQuickScoreResponse {
    score_1000: number;
    go_nogo: string;
    why: string;
    how: string[];
    anchor_interpretations: Record<string, any>;
}

export interface STPFKellyResponse {
    score: number;
    signal: 'GO' | 'MODERATE' | 'CAUTION' | 'NO_GO';
    recommended_effort_percent: number;
    reason: string;
    action: string;
    kelly_fractions: { raw: number; safe: number };
    expected_value: number;
    grade: {
        score_1000: number;
        grade: string;
        label: string;
        description: string;
        action: string;
        kelly_hint: string;
        color: string;
    };
    inputs: Record<string, any>;
}

export interface STPFGradeResponse {
    score_1000: number;
    grade: string;
    label: string;
    description: string;
    action: string;
    kelly_hint: string;
    color: string;
}

export interface STPFToTResponse {
    success: boolean;
    worst: { scenario: string; score_1000: number; go_nogo: string };
    base: { scenario: string; score_1000: number; go_nogo: string };
    best: { scenario: string; score_1000: number; go_nogo: string };
    weighted_score: number;
    score_range: [number, number];
    recommendation: string;
    confidence: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface STPFMonteCarloResponse {
    success: boolean;
    n_simulations: number;
    mean: number;
    median: number;
    std: number;
    percentile_10: number;
    percentile_90: number;
    min_score: number;
    max_score: number;
    go_probability: number;
    consider_probability: number;
    nogo_probability: number;
    distribution_summary: Record<string, number>;
    run_time_ms: number;
}

// Singleton instance
export const api = new ApiClient();

