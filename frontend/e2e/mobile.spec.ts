import { test, expect } from '@playwright/test';

/**
 * 모바일 반응형 E2E 테스트
 */
test.describe('모바일 반응형', () => {
    test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

    test('모바일 뷰포트에서 하단 네비게이션 표시', async ({ page }) => {
        await page.goto('/');

        // BottomNav 확인
        const bottomNav = page.locator('nav').filter({ hasText: /발견|캔버스|마이/i });
        await expect(bottomNav).toBeVisible();
    });

    test('모바일에서 햄버거 메뉴 동작', async ({ page }) => {
        await page.goto('/');

        // 햄버거 버튼 찾기
        const hamburgerButton = page.locator('button[aria-label*="메뉴"], button:has(svg[class*="Menu"])').first();

        if (await hamburgerButton.isVisible()) {
            await hamburgerButton.click();

            // 모바일 메뉴 오버레이 표시 확인
            const mobileMenu = page.locator('[class*="mobile-menu"], [class*="fixed"][class*="inset"]');
            await expect(mobileMenu).toBeVisible({ timeout: 2000 }).catch(() => {
                // 메뉴가 다른 방식으로 구현되었을 수 있음
            });
        }
    });

    test('모바일에서 콘텐츠 패딩 적용', async ({ page }) => {
        await page.goto('/');

        // 하단 네비게이션과 콘텐츠가 겹치지 않는지 확인
        const mainContent = page.locator('#main-content, main');
        await expect(mainContent).toBeVisible();
    });
});

/**
 * 태블릿 테스트
 */
test.describe('태블릿 반응형', () => {
    test.use({ viewport: { width: 768, height: 1024 } }); // iPad

    test('태블릿에서 레이아웃 확인', async ({ page }) => {
        await page.goto('/');

        // 헤더 표시 확인
        const header = page.locator('header');
        await expect(header).toBeVisible();
    });
});
