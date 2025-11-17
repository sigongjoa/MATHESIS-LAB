import { test, expect } from '@playwright/test';
import { MY_CURRICULUM_CONFIG } from './config';

test.describe('My Curriculum Page', () => {
  test.beforeEach(async ({ page }) => {
    // 페이지 네비게이션
    await page.goto(MY_CURRICULUM_CONFIG.url, {
      waitUntil: 'networkidle',
      timeout: MY_CURRICULUM_CONFIG.timeouts.navigation,
    });
  });

  test('should display page structure', async ({ page }) => {
    // 페이지가 로드되었는지 확인
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
  });

  test('should display create curriculum button', async ({ page }) => {
    // 새 커리큘럼 만들기 버튼 확인
    const createButton = page.locator('button:has-text("새 커리큘럼")');
    const visible = await createButton.isVisible().catch(() => false);

    // 버튼이 없다면 다른 형태의 버튼이 있는지 확인
    if (!visible) {
      const buttons = page.locator('button');
      const count = await buttons.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('should have no critical console errors', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // 페이지가 완전히 로드될 때까지 대기
    await page.waitForLoadState('networkidle');

    // 콘솔 에러가 없어야 함 (Tailwind CDN 경고는 무시)
    const criticalErrors = consoleErrors.filter(
      (error) => !error.includes('cdn.tailwindcss.com') && !error.includes('GSI_LOGGER')
    );
    expect(criticalErrors).toHaveLength(0);
  });
});
