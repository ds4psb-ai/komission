/**
 * Shotlist Timeline - Phase 2
 * 
 * VDG shotlist sequence visualization
 */

import React, { useEffect, useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    Animated,
} from 'react-native';
import { VdgCoachingData, ShotGuide, KickTiming } from '../hooks/useCoachingWebSocket';

// ============================================================
// Types
// ============================================================

interface ShotlistTimelineProps {
    vdgData: VdgCoachingData | null;
    currentTime: number;  // seconds
    totalDuration: number;  // seconds
}

// ============================================================
// Component
// ============================================================

export function ShotlistTimeline({
    vdgData,
    currentTime,
    totalDuration,
}: ShotlistTimelineProps) {
    const [currentShot, setCurrentShot] = useState<ShotGuide | null>(null);
    const [upcomingKick, setUpcomingKick] = useState<KickTiming | null>(null);
    const pulseAnim = React.useRef(new Animated.Value(1)).current;

    // Find current shot based on time
    useEffect(() => {
        if (!vdgData?.shotlist_sequence) return;

        const shot = vdgData.shotlist_sequence.find(
            (s) => currentTime >= s.t_window[0] && currentTime < s.t_window[1]
        );
        setCurrentShot(shot || null);
    }, [currentTime, vdgData]);

    // Find upcoming kick
    useEffect(() => {
        if (!vdgData?.kick_timings) return;

        const kick = vdgData.kick_timings.find(
            (k) => k.t_sec > currentTime && k.t_sec - currentTime <= k.pre_alert_sec
        );
        setUpcomingKick(kick || null);

        // Pulse animation when kick is near
        if (kick) {
            Animated.loop(
                Animated.sequence([
                    Animated.timing(pulseAnim, {
                        toValue: 1.1,
                        duration: 300,
                        useNativeDriver: true,
                    }),
                    Animated.timing(pulseAnim, {
                        toValue: 1,
                        duration: 300,
                        useNativeDriver: true,
                    }),
                ])
            ).start();
        } else {
            pulseAnim.setValue(1);
        }
    }, [currentTime, vdgData, pulseAnim]);

    if (!vdgData) return null;

    const progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;

    return (
        <View style={styles.container}>
            {/* Progress Bar */}
            <View style={styles.progressContainer}>
                <View style={styles.progressTrack}>
                    <View style={[styles.progressFill, { width: `${progress}%` }]} />

                    {/* Kick markers */}
                    {vdgData.kick_timings.map((kick, i) => {
                        const kickPos = (kick.t_sec / totalDuration) * 100;
                        return (
                            <View
                                key={i}
                                style={[
                                    styles.kickMarker,
                                    { left: `${kickPos}%` },
                                    kick.type === 'end' && styles.kickMarkerEnd,
                                ]}
                            />
                        );
                    })}
                </View>
            </View>

            {/* Current Shot Guide */}
            {currentShot && (
                <View style={styles.shotGuide}>
                    <Text style={styles.shotIndex}>
                        📍 Shot {currentShot.index + 1}
                    </Text>
                    <Text style={styles.shotGuideText}>{currentShot.guide}</Text>
                </View>
            )}

            {/* Upcoming Kick Alert */}
            {upcomingKick && (
                <Animated.View
                    style={[
                        styles.kickAlert,
                        { transform: [{ scale: pulseAnim }] },
                        upcomingKick.type === 'end' && styles.kickAlertEnd,
                    ]}
                >
                    <Text style={styles.kickCue}>{upcomingKick.cue}</Text>
                    <Text style={styles.kickMessage}>{upcomingKick.message}</Text>
                    <Text style={styles.kickCountdown}>
                        {Math.ceil(upcomingKick.t_sec - currentTime)}초 후
                    </Text>
                </Animated.View>
            )}
        </View>
    );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
    container: {
        position: 'absolute',
        top: 60,
        left: 16,
        right: 16,
    },
    progressContainer: {
        marginBottom: 8,
    },
    progressTrack: {
        height: 4,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        borderRadius: 2,
        position: 'relative',
    },
    progressFill: {
        height: '100%',
        backgroundColor: '#8b5cf6',
        borderRadius: 2,
    },
    kickMarker: {
        position: 'absolute',
        top: -2,
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: '#f59e0b',
        marginLeft: -4,
    },
    kickMarkerEnd: {
        backgroundColor: '#ef4444',
    },
    shotGuide: {
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        borderRadius: 8,
        padding: 8,
        marginBottom: 8,
    },
    shotIndex: {
        color: '#8b5cf6',
        fontSize: 11,
        fontWeight: '600',
        marginBottom: 2,
    },
    shotGuideText: {
        color: '#fff',
        fontSize: 13,
    },
    kickAlert: {
        backgroundColor: 'rgba(245, 158, 11, 0.9)',
        borderRadius: 10,
        padding: 10,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    kickAlertEnd: {
        backgroundColor: 'rgba(239, 68, 68, 0.9)',
    },
    kickCue: {
        fontSize: 18,
    },
    kickMessage: {
        color: '#fff',
        fontSize: 14,
        fontWeight: '600',
        flex: 1,
        marginHorizontal: 10,
    },
    kickCountdown: {
        color: '#fff',
        fontSize: 12,
        opacity: 0.8,
    },
});

export default ShotlistTimeline;
