/**
 * Feedback Input - Phase 3
 * 
 * User feedback input for adaptive coaching
 */

import React, { useState } from 'react';
import {
    View,
    Text,
    TextInput,
    Pressable,
    StyleSheet,
    Animated,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import { AdaptiveResponse } from '../hooks/useCoachingWebSocket';

// ============================================================
// Types
// ============================================================

interface FeedbackInputProps {
    onSend: (text: string) => void;
    lastResponse: AdaptiveResponse | null;
    disabled?: boolean;
}

// ============================================================
// Component
// ============================================================

export function FeedbackInput({
    onSend,
    lastResponse,
    disabled = false,
}: FeedbackInputProps) {
    const [text, setText] = useState('');
    const [expanded, setExpanded] = useState(false);
    const responseAnim = React.useRef(new Animated.Value(0)).current;

    React.useEffect(() => {
        if (lastResponse) {
            Animated.sequence([
                Animated.timing(responseAnim, {
                    toValue: 1,
                    duration: 300,
                    useNativeDriver: true,
                }),
                Animated.delay(3000),
                Animated.timing(responseAnim, {
                    toValue: 0,
                    duration: 300,
                    useNativeDriver: true,
                }),
            ]).start();
        }
    }, [lastResponse, responseAnim]);

    const handleSend = () => {
        if (text.trim() && !disabled) {
            onSend(text.trim());
            setText('');
        }
    };

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={styles.container}
        >
            {/* Last Response Bubble */}
            {lastResponse && (
                <Animated.View
                    style={[
                        styles.responseBubble,
                        lastResponse.accepted ? styles.responseAccepted : styles.responseRejected,
                        { opacity: responseAnim },
                    ]}
                >
                    <Text style={styles.responseIcon}>
                        {lastResponse.accepted ? '✅' : '❌'}
                    </Text>
                    <View style={styles.responseContent}>
                        <Text style={styles.responseMessage}>{lastResponse.message}</Text>
                        {lastResponse.alternative && (
                            <Text style={styles.responseAlternative}>
                                💡 {lastResponse.alternative}
                            </Text>
                        )}
                    </View>
                </Animated.View>
            )}

            {/* Input Row */}
            <View style={styles.inputRow}>
                <Pressable
                    style={styles.expandButton}
                    onPress={() => setExpanded(!expanded)}
                >
                    <Text style={styles.expandIcon}>{expanded ? '⬇️' : '💬'}</Text>
                </Pressable>

                {expanded && (
                    <>
                        <TextInput
                            style={styles.textInput}
                            placeholder="피드백 입력... (예: 역광이 안 돼요)"
                            placeholderTextColor="rgba(255,255,255,0.4)"
                            value={text}
                            onChangeText={setText}
                            editable={!disabled}
                        />
                        <Pressable
                            style={[
                                styles.sendButton,
                                (!text.trim() || disabled) && styles.sendButtonDisabled,
                            ]}
                            onPress={handleSend}
                            disabled={!text.trim() || disabled}
                        >
                            <Text style={styles.sendIcon}>➤</Text>
                        </Pressable>
                    </>
                )}
            </View>

            {/* Quick Feedback Chips */}
            {expanded && (
                <View style={styles.chipsContainer}>
                    {['이거 안 돼요', '다른 방법은?', '더 쉽게 해주세요'].map((chip) => (
                        <Pressable
                            key={chip}
                            style={styles.chip}
                            onPress={() => onSend(chip)}
                            disabled={disabled}
                        >
                            <Text style={styles.chipText}>{chip}</Text>
                        </Pressable>
                    ))}
                </View>
            )}
        </KeyboardAvoidingView>
    );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
    container: {
        position: 'absolute',
        bottom: 100,
        left: 16,
        right: 16,
    },
    responseBubble: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        padding: 12,
        borderRadius: 12,
        marginBottom: 8,
    },
    responseAccepted: {
        backgroundColor: 'rgba(34, 197, 94, 0.9)',
    },
    responseRejected: {
        backgroundColor: 'rgba(239, 68, 68, 0.9)',
    },
    responseIcon: {
        fontSize: 18,
        marginRight: 8,
    },
    responseContent: {
        flex: 1,
    },
    responseMessage: {
        color: '#fff',
        fontSize: 14,
        fontWeight: '500',
    },
    responseAlternative: {
        color: 'rgba(255, 255, 255, 0.9)',
        fontSize: 12,
        marginTop: 6,
    },
    inputRow: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        borderRadius: 25,
        padding: 6,
    },
    expandButton: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    expandIcon: {
        fontSize: 18,
    },
    textInput: {
        flex: 1,
        color: '#fff',
        fontSize: 14,
        marginLeft: 10,
        paddingVertical: 8,
    },
    sendButton: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: '#8b5cf6',
        justifyContent: 'center',
        alignItems: 'center',
    },
    sendButtonDisabled: {
        backgroundColor: 'rgba(139, 92, 246, 0.4)',
    },
    sendIcon: {
        fontSize: 16,
        color: '#fff',
    },
    chipsContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        marginTop: 8,
        gap: 8,
    },
    chip: {
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 16,
    },
    chipText: {
        color: '#fff',
        fontSize: 12,
    },
});

export default FeedbackInput;
