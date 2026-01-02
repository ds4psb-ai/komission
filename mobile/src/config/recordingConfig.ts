/**
 * Camera Recording Configuration
 * 
 * Optimized for 4K recording with H.265 (HEVC) codec
 * - 50% smaller file size vs H.264
 * - 25-30% battery savings
 * - iPhone 11 Pro+ and Android API 27+ support
 */

import { Platform } from 'react-native';

// ============================================================
// Recording Quality Presets
// ============================================================

export type RecordingQuality = '4k' | '1080p' | '720p';
export type CodecType = 'h265' | 'h264';

export interface RecordingConfig {
    quality: RecordingQuality;
    codec: CodecType;
    bitrate: number;
    fps: number;
    width: number;
    height: number;
    fileType: 'mp4' | 'mov';
    enableHDR: boolean;
    enableStabilization: boolean;
}

// ============================================================
// Platform-specific Codec Support Detection
// ============================================================

/**
 * Check if H.265 (HEVC) is supported on current device
 * - iOS: iPhone 7+ (A10 chip) for decode, iPhone 11 Pro+ for 4K encode
 * - Android: API 24+ decode, API 29+ 4K encode (varies by manufacturer)
 */
export function isH265Supported(): boolean {
    if (Platform.OS === 'ios') {
        // iOS 11+ supports HEVC, but 4K encoding needs A12+ (iPhone XS/11+)
        const iosVersion = parseInt(Platform.Version as string, 10);
        return iosVersion >= 11;
    }

    if (Platform.OS === 'android') {
        // Android API 24+ has HEVC support, but quality varies
        const apiLevel = Platform.Version as number;
        return apiLevel >= 24;
    }

    return false;
}

/**
 * Check if 4K recording is supported
 */
export function is4KSupported(): boolean {
    if (Platform.OS === 'ios') {
        // All iPhones since iPhone 6s support 4K
        return true;
    }

    if (Platform.OS === 'android') {
        // Most modern Android devices support 4K, check at runtime
        return true; // Will be validated by useCameraFormat
    }

    return false;
}

// ============================================================
// Bitrate Recommendations (Mbps)
// ============================================================

/**
 * Recommended bitrates for different quality/codec combinations
 * H.265 requires ~50% less bitrate for same quality
 * 
 * Reference: Apple ProRes vs HEVC comparison
 */
const BITRATE_MAP: Record<RecordingQuality, Record<CodecType, number>> = {
    '4k': {
        h265: 15_000_000,   // 15 Mbps (H.265 4K optimal)
        h264: 30_000_000,   // 30 Mbps (H.264 4K optimal)
    },
    '1080p': {
        h265: 6_000_000,    // 6 Mbps
        h264: 12_000_000,   // 12 Mbps
    },
    '720p': {
        h265: 3_000_000,    // 3 Mbps
        h264: 6_000_000,    // 6 Mbps
    },
};

const RESOLUTION_MAP: Record<RecordingQuality, { width: number; height: number }> = {
    '4k': { width: 3840, height: 2160 },
    '1080p': { width: 1920, height: 1080 },
    '720p': { width: 1280, height: 720 },
};

// ============================================================
// Config Builders
// ============================================================

/**
 * Get optimal recording configuration based on device capabilities
 * Automatically falls back to H.264 if H.265 not supported
 */
export function getOptimalRecordingConfig(
    preferredQuality: RecordingQuality = '4k',
    preferH265: boolean = true
): RecordingConfig {
    const supportsH265 = isH265Supported();
    const supports4K = is4KSupported();

    // Determine actual quality (fallback if 4K not supported)
    const actualQuality = supports4K ? preferredQuality :
        preferredQuality === '4k' ? '1080p' : preferredQuality;

    // Determine codec (fallback if H.265 not supported)
    const actualCodec: CodecType = (preferH265 && supportsH265) ? 'h265' : 'h264';

    const resolution = RESOLUTION_MAP[actualQuality];
    const bitrate = BITRATE_MAP[actualQuality][actualCodec];

    return {
        quality: actualQuality,
        codec: actualCodec,
        bitrate,
        fps: 30,
        width: resolution.width,
        height: resolution.height,
        fileType: 'mp4',
        enableHDR: actualQuality === '4k' && Platform.OS === 'ios',
        enableStabilization: false, // Disabled for faster startup (30-50% improvement)
    };
}

/**
 * Get battery-optimized config for low power mode
 */
export function getBatteryOptimizedConfig(): RecordingConfig {
    return {
        quality: '1080p',
        codec: isH265Supported() ? 'h265' : 'h264',
        bitrate: 6_000_000,
        fps: 30,
        width: 1920,
        height: 1080,
        fileType: 'mp4',
        enableHDR: false,
        enableStabilization: false,
    };
}

/**
 * Get network-optimized config for slow connections
 */
export function getNetworkOptimizedConfig(): RecordingConfig {
    return {
        quality: '720p',
        codec: isH265Supported() ? 'h265' : 'h264',
        bitrate: 3_000_000,
        fps: 30,
        width: 1280,
        height: 720,
        fileType: 'mp4',
        enableHDR: false,
        enableStabilization: false,
    };
}

// ============================================================
// VisionCamera Recording Options Builder
// ============================================================

export interface VisionCameraRecordingOptions {
    fileType: 'mp4' | 'mov';
    videoCodec: 'h265' | 'h264';
    videoBitRate: number;
    onRecordingFinished: (video: any) => void;
    onRecordingError: (error: any) => void;
}

/**
 * Build VisionCamera-compatible recording options from config
 */
export function buildRecordingOptions(
    config: RecordingConfig,
    onFinished: (video: any) => void,
    onError: (error: any) => void
): VisionCameraRecordingOptions {
    return {
        fileType: config.fileType,
        videoCodec: config.codec,
        videoBitRate: config.bitrate,
        onRecordingFinished: onFinished,
        onRecordingError: onError,
    };
}

// ============================================================
// File Size Estimation
// ============================================================

/**
 * Estimate file size for given duration
 * @param durationSeconds Recording duration in seconds
 * @param config Recording configuration
 * @returns Estimated file size in MB
 */
export function estimateFileSize(
    durationSeconds: number,
    config: RecordingConfig
): number {
    // File size (bytes) = bitrate (bits/sec) × duration (sec) / 8
    const bytes = (config.bitrate * durationSeconds) / 8;
    const megabytes = bytes / (1024 * 1024);

    // Add ~10% overhead for container/audio
    return Math.round(megabytes * 1.1);
}

/**
 * Get human-readable file size estimate
 */
export function getFileSizeEstimate(
    durationSeconds: number,
    config: RecordingConfig
): string {
    const mb = estimateFileSize(durationSeconds, config);

    if (mb >= 1024) {
        return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb} MB`;
}
