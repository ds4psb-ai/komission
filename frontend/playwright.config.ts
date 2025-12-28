import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration (PEGL v1.0)
 * 
 * 핵심 사용자 플로우 검증
 * - 메인 페이지 로딩
 * - 네비게이션
 * - Canvas 기본 동작
 * - 모바일 반응형
 */

export default defineConfig({
    testDir: './e2e',

    /* 병렬 실행 */
    fullyParallel: true,

    /* CI에서 재시도 */
    retries: process.env.CI ? 2 : 0,

    /* Reporter */
    reporter: [
        ['html', { open: 'never' }],
        ['list']
    ],

    /* 테스트 타임아웃 */
    timeout: 30000,

    /* 공통 설정 */
    use: {
        /* 기본 URL */
        baseURL: 'http://localhost:3000',

        /* 스크린샷 (실패 시) */
        screenshot: 'only-on-failure',

        /* 비디오 (실패 시) */
        video: 'retain-on-failure',

        /* 트레이스 (재시도 시) */
        trace: 'on-first-retry',
    },

    /* 프로젝트 (브라우저별) */
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
        {
            name: 'mobile-chrome',
            use: { ...devices['Pixel 5'] },
        },
    ],

    /* 개발 서버 자동 시작 (선택) */
    // webServer: {
    //   command: 'npm run dev',
    //   url: 'http://localhost:3000',
    //   reuseExistingServer: !process.env.CI,
    // },
});
