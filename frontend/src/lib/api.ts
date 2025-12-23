/**
 * Komission API Client
 * Handles all backend API communication
 */

const API_BASE_URL = ''; // Use relative path to leverage Next.js proxy


interface ApiError {
    detail: string;
}

class ApiClient {
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

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            // Handle token expiration (401 Unauthorized)
            if (response.status === 401) {
                console.warn('[API] Token expired or invalid, logging out...');
                this.clearToken();

                // Redirect to login page (only in browser)
                if (typeof window !== 'undefined') {
                    // Avoid redirect loop if already on login page
                    if (!window.location.pathname.includes('/login')) {
                        window.location.href = '/login?expired=true';
                    }
                }
                throw new Error('세션이 만료되었습니다. 다시 로그인해 주세요.');
            }

            const error: ApiError = await response.json().catch(() => ({
                detail: '오류가 발생했습니다.',
            }));
            throw new Error(error.detail);
        }

        return response.json();
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

    // O2O Locations
    async listO2OLocations() {
        return this.request<O2OLocation[]>('/api/v1/o2o/locations');
    }

    async listO2OCampaigns() {
        return this.request<O2OCampaign[]>('/api/v1/o2o/campaigns');
    }

    async applyO2OCampaign(campaignId: string) {
        return this.request<O2OApplication>(`/api/v1/o2o/campaigns/${campaignId}/apply`, {
            method: 'POST',
        });
    }

    async listMyO2OApplications() {
        return this.request<O2OApplication[]>('/api/v1/o2o/applications/me');
    }

    async verifyLocation(locationId: string, lat: number, lng: number) {
        return this.request<{
            status: string;
            points_awarded: number;
            total_points: number;
            distance: number;
            message: string;
        }>('/api/v1/o2o/verify', {
            method: 'POST',
            body: JSON.stringify({ location_id: locationId, lat, lng }),
        });
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

    // Health
    async health() {
        return this.request<{ status: string; version: string }>('/health');
    }
}

// Types
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
    completed_at: string | null;
}

export interface MissionCompleteResponse {
    status: string;
    mission_type?: string;
    points_earned: number;
    total_k_points?: number;
}

export interface GamificationLeaderboardEntry {
    rank: number;
    user_id: string;
    user_name: string | null;
    profile_image: string | null;
    total_royalty: number;
    streak_days: number;
    badge_count: number;
}

// Singleton instance
export const api = new ApiClient();
