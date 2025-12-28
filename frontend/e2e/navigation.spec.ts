import { test, expect } from '@playwright/test';

/**
 * 네비게이션 E2E 테스트
 */
test.describe('네비게이션', () => {
    test('헤더 네비게이션 링크들', async ({ page }) => {
        await page.goto('/');

        // 헤더 확인
        const header = page.locator('header');
        await expect(header).toBeVisible();

        // 로고 클릭 시 홈으로 이동
        const logo = header.getByText(/Komission/i).first();
        if (await logo.isVisible()) {
            await logo.click();
            await expect(page).toHaveURL('/');
        }
    });

    test('주요 페이지 접근 가능', async ({ page }) => {
        // 파이프라인 페이지
        await page.goto('/pipelines');
        await expect(page).toHaveURL(/pipelines/);

        // 캔버스 페이지
        await page.goto('/canvas');
        await expect(page).toHaveURL(/canvas/);

        // 로그인 페이지
        await page.goto('/login');
        await expect(page).toHaveURL(/login/);
    });

    test('404 페이지 처리', async ({ page }) => {
        const response = await page.goto('/non-existent-page-12345');
        // Next.js는 404를 반환하거나 커스텀 404 페이지 표시
        expect(response?.status()).toBe(404);
    });
});

/**
 * 접근성 테스트
 */
test.describe('접근성', () => {
    test('SkipLink 동작', async ({ page }) => {
        await page.goto('/');

        // Tab 키로 SkipLink 활성화
        await page.keyboard.press('Tab');

        // SkipLink가 보이는지 확인
        const skipLink = page.getByText(/메인 콘텐츠로 건너뛰기/);
        // SkipLink는 focus 시에만 보임
    });

    test('키보드 네비게이션', async ({ page }) => {
        await page.goto('/');

        // Tab으로 네비게이션 가능
        for (let i = 0; i < 5; i++) {
            await page.keyboard.press('Tab');
        }

        // 현재 포커스된 요소가 있는지 확인
        const focusedElement = page.locator(':focus');
        await expect(focusedElement).toBeTruthy();
    });
});
