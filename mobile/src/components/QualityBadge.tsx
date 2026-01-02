/**
 * Quality Badge Component
 * 
 * Displays current recording quality and codec
 * with visual indicators for 4K/H.265 support
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface QualityBadgeProps {
    quality: '4k' | '1080p' | '720p';
    codec: 'h265' | 'h264';
    hasH265: boolean;
    has4K: boolean;
}

export function QualityBadge({
    quality,
    codec,
    hasH265,
    has4K,
}: QualityBadgeProps) {
    // Format quality display
    const qualityLabel = quality.toUpperCase();
    const codecLabel = codec === 'h265' ? 'HEVC' : 'H.264';

    // Determine badge color based on quality
    const getBadgeColor = () => {
        if (quality === '4k' && codec === 'h265') {
            return styles.badgePremium; // Gold - best quality
        }
        if (quality === '4k') {
            return styles.badge4K; // Blue - 4K but H.264
        }
        if (quality === '1080p') {
            return styles.badgeHD; // Gray - HD
        }
        return styles.badgeSD; // Dark gray - SD
    };

    return (
        <View style={styles.container}>
            {/* Quality Badge */}
            <View style={[styles.badge, getBadgeColor()]}>
                <Text style={styles.qualityText}>{qualityLabel}</Text>
            </View>

            {/* Codec Badge */}
            <View style={[styles.codecBadge, codec === 'h265' && styles.codecH265]}>
                <Text style={styles.codecText}>{codecLabel}</Text>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
    },
    badge: {
        paddingVertical: 4,
        paddingHorizontal: 10,
        borderRadius: 6,
    },
    badgePremium: {
        backgroundColor: 'rgba(234, 179, 8, 0.9)', // Gold
    },
    badge4K: {
        backgroundColor: 'rgba(59, 130, 246, 0.9)', // Blue
    },
    badgeHD: {
        backgroundColor: 'rgba(107, 114, 128, 0.9)', // Gray
    },
    badgeSD: {
        backgroundColor: 'rgba(75, 85, 99, 0.9)', // Dark gray
    },
    qualityText: {
        color: '#fff',
        fontSize: 12,
        fontWeight: '700',
    },
    codecBadge: {
        paddingVertical: 4,
        paddingHorizontal: 8,
        borderRadius: 6,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.2)',
    },
    codecH265: {
        borderColor: 'rgba(34, 197, 94, 0.6)', // Green border for HEVC
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
    },
    codecText: {
        color: '#fff',
        fontSize: 10,
        fontWeight: '600',
    },
});
