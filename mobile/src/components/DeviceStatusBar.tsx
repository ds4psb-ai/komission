/**
 * Device Status Bar Component
 * 
 * Shows warnings and device status during recording setup
 * - Battery level warnings
 * - Storage warnings  
 * - Network status
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

interface DeviceStatusBarProps {
    warnings: string[];
    batteryLevel: number;
    batteryCharging: boolean;
}

export function DeviceStatusBar({
    warnings,
    batteryLevel,
    batteryCharging,
}: DeviceStatusBarProps) {
    if (warnings.length === 0) return null;

    const getBatteryIcon = () => {
        if (batteryCharging) return '🔌';
        if (batteryLevel > 0.5) return '🔋';
        if (batteryLevel > 0.2) return '🪫';
        return '⚠️';
    };

    const getBatteryColor = () => {
        if (batteryCharging) return styles.batteryCharging;
        if (batteryLevel > 0.5) return styles.batteryGood;
        if (batteryLevel > 0.2) return styles.batteryLow;
        return styles.batteryCritical;
    };

    return (
        <View style={styles.container}>
            {/* Battery indicator */}
            <View style={[styles.batteryContainer, getBatteryColor()]}>
                <Text style={styles.batteryIcon}>{getBatteryIcon()}</Text>
                <Text style={styles.batteryText}>
                    {Math.round(batteryLevel * 100)}%
                </Text>
            </View>

            {/* Warnings */}
            <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.warningsContent}
            >
                {warnings.map((warning, index) => (
                    <View key={index} style={styles.warningBadge}>
                        <Text style={styles.warningText}>{warning}</Text>
                    </View>
                ))}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        marginHorizontal: 16,
        marginTop: 12,
    },
    batteryContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        alignSelf: 'flex-start',
        paddingVertical: 4,
        paddingHorizontal: 10,
        borderRadius: 12,
        marginBottom: 8,
    },
    batteryGood: {
        backgroundColor: 'rgba(34, 197, 94, 0.3)',
    },
    batteryLow: {
        backgroundColor: 'rgba(245, 158, 11, 0.3)',
    },
    batteryCritical: {
        backgroundColor: 'rgba(239, 68, 68, 0.3)',
    },
    batteryCharging: {
        backgroundColor: 'rgba(59, 130, 246, 0.3)',
    },
    batteryIcon: {
        fontSize: 14,
        marginRight: 4,
    },
    batteryText: {
        color: '#fff',
        fontSize: 12,
        fontWeight: '600',
    },
    warningsContent: {
        flexDirection: 'row',
        gap: 8,
    },
    warningBadge: {
        backgroundColor: 'rgba(245, 158, 11, 0.2)',
        borderWidth: 1,
        borderColor: 'rgba(245, 158, 11, 0.4)',
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 8,
    },
    warningText: {
        color: 'rgba(255, 255, 255, 0.9)',
        fontSize: 12,
    },
});
