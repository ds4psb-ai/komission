/**
 * Event Tracking Utility
 * 
 * Tracks creator behavior for RL policy improvement.
 * Buffers events and sends in batches for efficiency.
 */

type EventType =
    | 'page_view'
    | 'template_click'
    | 'video_watch'
    | 'camera_open'
    | 'form_start'
    | 'form_submit'
    | 'share'
    | 'promote_click'
    | 'apply_click'
    | 'card_click';

interface TrackEvent {
    event_type: EventType;
    resource_type?: string;
    resource_id?: string;
    metadata?: Record<string, unknown>;
    timestamp?: string;
}

interface EventTrackerConfig {
    batchSize: number;
    flushInterval: number; // ms
    enabled: boolean;
}

class EventTracker {
    private buffer: TrackEvent[] = [];
    private sessionId: string;
    private config: EventTrackerConfig;
    private flushTimer: ReturnType<typeof setInterval> | null = null;

    constructor(config?: Partial<EventTrackerConfig>) {
        this.config = {
            batchSize: 10,
            flushInterval: 30000, // 30 seconds
            enabled: true,
            ...config,
        };
        this.sessionId = this.generateSessionId();
        this.startFlushTimer();

        // Flush on page unload
        if (typeof window !== 'undefined') {
            window.addEventListener('beforeunload', () => this.flush());
        }
    }

    private generateSessionId(): string {
        return `sess_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    }

    private startFlushTimer() {
        if (this.flushTimer) clearInterval(this.flushTimer);
        this.flushTimer = setInterval(() => this.flush(), this.config.flushInterval);
    }

    /**
     * Track an event
     */
    track(
        eventType: EventType,
        resourceType?: string,
        resourceId?: string,
        metadata?: Record<string, unknown>
    ) {
        if (!this.config.enabled) return;

        const event: TrackEvent = {
            event_type: eventType,
            resource_type: resourceType,
            resource_id: resourceId,
            metadata,
            timestamp: new Date().toISOString(),
        };

        this.buffer.push(event);

        if (this.buffer.length >= this.config.batchSize) {
            this.flush();
        }
    }

    /**
     * Convenience method for page view
     */
    pageView(pageType: string, pageId?: string) {
        this.track('page_view', pageType, pageId);
    }

    /**
     * Track video watch progress
     */
    videoWatch(videoId: string, watchSeconds: number, completed: boolean = false) {
        this.track('video_watch', 'video', videoId, { watch_seconds: watchSeconds, completed });
    }

    /**
     * Track card click
     */
    cardClick(cardType: string, cardId: string) {
        this.track('card_click', cardType, cardId);
    }

    /**
     * Flush buffered events to server
     */
    async flush() {
        if (this.buffer.length === 0) return;

        const events = [...this.buffer];
        this.buffer = [];

        try {
            const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
            const headers: HeadersInit = {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            };

            await fetch('/api/v1/events/track', {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    events,
                    session_id: this.sessionId,
                }),
            });
        } catch (error) {
            // Re-add events to buffer on failure (simple retry)
            console.warn('Failed to flush events:', error);
            this.buffer = [...events, ...this.buffer].slice(0, 100); // Keep max 100
        }
    }

    /**
     * Get current session ID
     */
    getSessionId(): string {
        return this.sessionId;
    }

    /**
     * Disable tracking (e.g., for testing)
     */
    disable() {
        this.config.enabled = false;
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
            this.flushTimer = null;
        }
    }

    /**
     * Enable tracking
     */
    enable() {
        this.config.enabled = true;
        this.startFlushTimer();
    }
}

// Singleton instance
export const tracker = new EventTracker();

// Convenience exports
export const trackEvent = tracker.track.bind(tracker);
export const trackPageView = tracker.pageView.bind(tracker);
export const trackVideoWatch = tracker.videoWatch.bind(tracker);
export const trackCardClick = tracker.cardClick.bind(tracker);
