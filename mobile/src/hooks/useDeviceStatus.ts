/**
 * Device Status Monitoring Hook
 * 
 * Monitors device status for adaptive recording quality:
 * - Battery level and charging status
 * - Network type and quality
 * - Storage availability
 * 
 * Automatically adjusts recording config based on device state
 */

import { useState, useEffect, useCallback } from 'react';
import { Platform, AppState, AppStateStatus } from 'react-native';
import * as Battery from 'expo-battery';
import * as Network from 'expo-network';
import * as FileSystem from 'expo-file-system';
import {
    RecordingConfig,
    getOptimalRecordingConfig,
    getBatteryOptimizedConfig,
    getNetworkOptimizedConfig,
} from '@/config/recordingConfig';

// ============================================================
// Types
// ============================================================

export interface DeviceStatus {
    // Battery
    batteryLevel: number; // 0-1
    batteryCharging: boolean;
    isLowPowerMode: boolean;

    // Network
    networkType: 'wifi' | 'cellular' | 'none';
    isConnected: boolean;

    // Storage
    availableStorageGB: number;

    // Overall
    isReady: boolean;
    recommendedConfig: RecordingConfig;
    warnings: string[];
}

// ============================================================
// Thresholds
// ============================================================

const BATTERY_LOW_THRESHOLD = 0.2; // 20%
const BATTERY_CRITICAL_THRESHOLD = 0.1; // 10%
const STORAGE_LOW_THRESHOLD_GB = 1; // 1GB
const STORAGE_CRITICAL_THRESHOLD_GB = 0.5; // 500MB

// ============================================================
// Hook
// ============================================================

export function useDeviceStatus(): DeviceStatus {
    const [status, setStatus] = useState<DeviceStatus>({
        batteryLevel: 1,
        batteryCharging: false,
        isLowPowerMode: false,
        networkType: 'wifi',
        isConnected: true,
        availableStorageGB: 10,
        isReady: false,
        recommendedConfig: getOptimalRecordingConfig(),
        warnings: [],
    });

    // Check battery status
    const checkBattery = useCallback(async () => {
        try {
            const level = await Battery.getBatteryLevelAsync();
            const state = await Battery.getBatteryStateAsync();
            const powerMode = await Battery.isLowPowerModeEnabledAsync();

            return {
                batteryLevel: level,
                batteryCharging: state === Battery.BatteryState.CHARGING,
                isLowPowerMode: powerMode,
            };
        } catch {
            return {
                batteryLevel: 1,
                batteryCharging: false,
                isLowPowerMode: false,
            };
        }
    }, []);

    // Check network status
    const checkNetwork = useCallback(async () => {
        try {
            const state = await Network.getNetworkStateAsync();

            let networkType: 'wifi' | 'cellular' | 'none' = 'none';
            if (state.type === Network.NetworkStateType.WIFI) {
                networkType = 'wifi';
            } else if (
                state.type === Network.NetworkStateType.CELLULAR
            ) {
                networkType = 'cellular';
            }

            return {
                networkType,
                isConnected: state.isInternetReachable ?? false,
            };
        } catch {
            return {
                networkType: 'wifi' as const,
                isConnected: true,
            };
        }
    }, []);

    // Check storage
    const checkStorage = useCallback(async () => {
        try {
            const info = await FileSystem.getFreeDiskStorageAsync();
            const gb = info / (1024 * 1024 * 1024);
            return { availableStorageGB: gb };
        } catch {
            return { availableStorageGB: 10 };
        }
    }, []);

    // Determine recommended config based on device status
    const getRecommendedConfig = useCallback(
        (
            batteryLevel: number,
            isLowPowerMode: boolean,
            networkType: string,
            storageGB: number
        ): { config: RecordingConfig; warnings: string[] } => {
            const warnings: string[] = [];

            // Critical battery - force low quality
            if (batteryLevel < BATTERY_CRITICAL_THRESHOLD) {
                warnings.push('배터리 부족! 720p 모드로 전환됩니다.');
                return { config: getNetworkOptimizedConfig(), warnings };
            }

            // Low battery or power mode - battery optimized
            if (batteryLevel < BATTERY_LOW_THRESHOLD || isLowPowerMode) {
                warnings.push('저전력 모드: 1080p로 촬영합니다.');
                return { config: getBatteryOptimizedConfig(), warnings };
            }

            // Critical storage
            if (storageGB < STORAGE_CRITICAL_THRESHOLD_GB) {
                warnings.push('저장 공간 부족! 촬영이 제한될 수 있습니다.');
                return { config: getNetworkOptimizedConfig(), warnings };
            }

            // Low storage - warn but allow 4K
            if (storageGB < STORAGE_LOW_THRESHOLD_GB) {
                warnings.push('저장 공간이 부족합니다. (잔여: ' + storageGB.toFixed(1) + 'GB)');
            }

            // Cellular network - consider bandwidth
            if (networkType === 'cellular') {
                warnings.push('셀룰러 네트워크: 실시간 코칭이 지연될 수 있습니다.');
            }

            // No network
            if (networkType === 'none') {
                warnings.push('네트워크 없음: 코칭 없이 촬영만 가능합니다.');
            }

            // All good - use 4K
            return { config: getOptimalRecordingConfig('4k', true), warnings };
        },
        []
    );

    // Update all status
    const updateStatus = useCallback(async () => {
        const battery = await checkBattery();
        const network = await checkNetwork();
        const storage = await checkStorage();

        const { config, warnings } = getRecommendedConfig(
            battery.batteryLevel,
            battery.isLowPowerMode,
            network.networkType,
            storage.availableStorageGB
        );

        setStatus({
            ...battery,
            ...network,
            ...storage,
            isReady: true,
            recommendedConfig: config,
            warnings,
        });
    }, [checkBattery, checkNetwork, checkStorage, getRecommendedConfig]);

    // Initial check and app state listener
    useEffect(() => {
        updateStatus();

        // Re-check when app becomes active
        const subscription = AppState.addEventListener(
            'change',
            (state: AppStateStatus) => {
                if (state === 'active') {
                    updateStatus();
                }
            }
        );

        // Battery listener
        const batterySubscription = Battery.addBatteryLevelListener(({ batteryLevel }) => {
            if (batteryLevel < BATTERY_LOW_THRESHOLD) {
                updateStatus();
            }
        });

        return () => {
            subscription.remove();
            batterySubscription.remove();
        };
    }, [updateStatus]);

    return status;
}

// ============================================================
// Utility Functions
// ============================================================

/**
 * Format battery percentage for display
 */
export function formatBatteryLevel(level: number): string {
    return `${Math.round(level * 100)}%`;
}

/**
 * Format storage for display
 */
export function formatStorage(gb: number): string {
    if (gb >= 1) {
        return `${gb.toFixed(1)} GB`;
    }
    return `${Math.round(gb * 1024)} MB`;
}

/**
 * Get battery icon based on level
 */
export function getBatteryIcon(level: number, charging: boolean): string {
    if (charging) return '🔌';
    if (level > 0.8) return '🔋';
    if (level > 0.5) return '🔋';
    if (level > 0.2) return '🪫';
    return '⚠️';
}
