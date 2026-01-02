import { View, Text, StyleSheet, Pressable, Linking } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function HomeScreen() {
    const router = useRouter();

    const openWebApp = () => {
        // 웹앱으로 이동 (딥링크)
        Linking.openURL('https://komission.app');
    };

    return (
        <SafeAreaView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.logo}>KOMISSION</Text>
                <Text style={styles.subtitle}>AI 촬영 코칭</Text>
            </View>

            <View style={styles.content}>
                <Pressable
                    style={styles.mainButton}
                    onPress={() => router.push('/camera')}
                >
                    <Text style={styles.mainButtonIcon}>🎬</Text>
                    <Text style={styles.mainButtonText}>4K 촬영 시작</Text>
                    <Text style={styles.mainButtonSubtext}>AI 코칭과 함께 촬영하기</Text>
                </Pressable>

                <Pressable style={styles.webButton} onPress={openWebApp}>
                    <Text style={styles.webButtonText}>🌐 웹앱에서 더 많은 기능 보기</Text>
                </Pressable>
            </View>

            <View style={styles.footer}>
                <Text style={styles.footerText}>
                    아웃라이어 분석, 체험단은{'\n'}웹앱에서 확인하세요
                </Text>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#000',
    },
    header: {
        alignItems: 'center',
        paddingTop: 60,
        paddingBottom: 40,
    },
    logo: {
        fontSize: 32,
        fontWeight: '800',
        color: '#fff',
        letterSpacing: 4,
    },
    subtitle: {
        fontSize: 14,
        color: 'rgba(255,255,255,0.5)',
        marginTop: 8,
    },
    content: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingHorizontal: 24,
    },
    mainButton: {
        width: '100%',
        backgroundColor: 'rgba(59, 130, 246, 0.15)',
        borderWidth: 1,
        borderColor: 'rgba(59, 130, 246, 0.4)',
        borderRadius: 20,
        paddingVertical: 32,
        paddingHorizontal: 24,
        alignItems: 'center',
    },
    mainButtonIcon: {
        fontSize: 48,
        marginBottom: 16,
    },
    mainButtonText: {
        fontSize: 24,
        fontWeight: '700',
        color: '#fff',
        marginBottom: 8,
    },
    mainButtonSubtext: {
        fontSize: 14,
        color: 'rgba(255,255,255,0.6)',
    },
    webButton: {
        marginTop: 24,
        paddingVertical: 16,
        paddingHorizontal: 24,
    },
    webButtonText: {
        fontSize: 14,
        color: 'rgba(255,255,255,0.5)',
        textDecorationLine: 'underline',
    },
    footer: {
        paddingBottom: 40,
        alignItems: 'center',
    },
    footerText: {
        fontSize: 12,
        color: 'rgba(255,255,255,0.3)',
        textAlign: 'center',
        lineHeight: 18,
    },
});
