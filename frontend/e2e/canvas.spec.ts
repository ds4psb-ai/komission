import { test, expect } from '@playwright/test';

/**
 * Canvas 페이지 E2E 테스트
 */
test.describe('Canvas 페이지', () => {
    test('Canvas 페이지 로딩', async ({ page }) => {
        await page.goto('/canvas');

        // 페이지 로딩 확인
        await expect(page).toHaveURL(/canvas/);

        // React Flow 컨테이너 확인
        const reactFlowContainer = page.locator('.react-flow, [class*="react-flow"]');
        await expect(reactFlowContainer).toBeVisible({ timeout: 10000 });
    });

    test('사이드바 노드 패널 확인', async ({ page }) => {
        await page.goto('/canvas');

        // 사이드바 확인
        const sidebar = page.locator('aside, [class*="sidebar"]');
        await expect(sidebar).toBeVisible({ timeout: 10000 });

        // 노드 타입 버튼들 확인
        const nodeButtons = page.locator('aside button, aside [draggable="true"]');
        const count = await nodeButtons.count();
        expect(count).toBeGreaterThan(0);
    });

    test('모드 토글 (Simple/Pro)', async ({ page }) => {
        await page.goto('/canvas');

        // 모드 토글 버튼 찾기
        const simpleButton = page.getByText(/Simple/i);
        const proButton = page.getByText(/Pro/i);

        if (await simpleButton.isVisible()) {
            await simpleButton.click();
        }

        if (await proButton.isVisible()) {
            await proButton.click();
        }
    });

    test('Canvas 컨트롤 버튼 확인', async ({ page }) => {
        await page.goto('/canvas');

        // React Flow Controls 확인
        const controls = page.locator('.react-flow__controls');
        await expect(controls).toBeVisible({ timeout: 10000 });
    });
});
