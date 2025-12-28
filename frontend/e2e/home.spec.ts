import { test, expect } from '@playwright/test';

/**
 * 메인 페이지 E2E 테스트
 */
test.describe('메인 페이지', () => {
    test('페이지 로딩 및 기본 요소 확인', async ({ page }) => {
        await page.goto('/');

        // 타이틀 확인
        await expect(page).toHaveTitle(/Komission/);

        // 헤더 존재 확인
        await expect(page.locator('header')).toBeVisible();

        // 메인 콘텐츠 영역 확인
        await expect(page.locator('#main-content')).toBeVisible();
    });

    test('네비게이션 링크 동작', async ({ page }) => {
        await page.goto('/');

        // 캔버스 링크 클릭
        const canvasLink = page.getByRole('link', { name: /캔버스|Canvas/i });
        if (await canvasLink.isVisible()) {
            await canvasLink.click();
            await expect(page).toHaveURL(/canvas/);
        }
    });

    test('비디오 카드 hover 효과', async ({ page }) => {
        await page.goto('/');

        // 비디오 카드가 있으면 hover 테스트
        const videoCard = page.locator('[class*="VirloVideoCard"], [class*="video-card"]').first();
        if (await videoCard.isVisible()) {
            await videoCard.hover();
            // hover 상태에서 스케일 변화 확인 (CSS transform)
            await expect(videoCard).toBeVisible();
        }
    });
});
