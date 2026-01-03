/**
 * Outlier Components - Shared components for outlier display and interaction
 */

export { TikTokPlayer, TikTokHoverPreview, extractTikTokVideoId, extractVideoId, detectPlatform, getProxiedThumbnailUrl } from './TikTokPlayer';
export { TierBadge } from './TierBadge';
export { OutlierScoreBadge } from './OutlierScoreBadge';
export { PlatformBadge } from './PlatformBadge';
export { OutlierMetrics } from './OutlierMetrics';
export { PipelineStatus, getPipelineStage } from './PipelineStatus';
export { FilmingGuide } from './FilmingGuide';
export { OutlierDetailModal } from './OutlierDetailModal';

// Shared card components (to ensure consistency across different card UIs)
export { OutlierCardFooter, formatRelativeTime } from './OutlierCardFooter';
export { ViewCountBadge, formatViewCount } from './ViewCountBadge';

// Language Gate
export { LanguageGateBadge } from './LanguageGateBadge';
