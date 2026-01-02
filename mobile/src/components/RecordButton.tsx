import React from 'react';
import { Pressable, View, StyleSheet, Animated } from 'react-native';

interface RecordButtonProps {
    isRecording: boolean;
    onPress: () => void;
}

export function RecordButton({ isRecording, onPress }: RecordButtonProps) {
    const scaleAnim = React.useRef(new Animated.Value(1)).current;

    // Pulse animation when recording
    React.useEffect(() => {
        if (isRecording) {
            const pulse = Animated.loop(
                Animated.sequence([
                    Animated.timing(scaleAnim, {
                        toValue: 1.1,
                        duration: 500,
                        useNativeDriver: true,
                    }),
                    Animated.timing(scaleAnim, {
                        toValue: 1,
                        duration: 500,
                        useNativeDriver: true,
                    }),
                ])
            );
            pulse.start();
            return () => pulse.stop();
        } else {
            scaleAnim.setValue(1);
        }
    }, [isRecording, scaleAnim]);

    return (
        <Pressable onPress={onPress} style={styles.container}>
            <Animated.View
                style={[
                    styles.outerRing,
                    isRecording && styles.outerRingRecording,
                    { transform: [{ scale: scaleAnim }] },
                ]}
            >
                <View
                    style={[
                        styles.innerButton,
                        isRecording && styles.innerButtonRecording,
                    ]}
                />
            </Animated.View>
        </Pressable>
    );
}

const styles = StyleSheet.create({
    container: {
        padding: 10,
    },
    outerRing: {
        width: 80,
        height: 80,
        borderRadius: 40,
        borderWidth: 4,
        borderColor: '#fff',
        justifyContent: 'center',
        alignItems: 'center',
    },
    outerRingRecording: {
        borderColor: '#ef4444',
    },
    innerButton: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: '#ef4444',
    },
    innerButtonRecording: {
        width: 30,
        height: 30,
        borderRadius: 6,
        backgroundColor: '#ef4444',
    },
});
