import { test, expect } from '@playwright/test';
import { HOME_CONFIG } from './config';

test.describe('Home (My Curriculum) Page', () => {
  test.beforeEach(async ({ page }) => {
    // 페이지 네비게이션
    await page.goto(HOME_CONFIG.url, {
      waitUntil: 'networkidle',
      timeout: HOME_CONFIG.timeouts.navigation,
    });
  });

  test('should display MATHESIS LAB header', async ({ page }) => {
    // 로고 확인
    const logo = page.locator('text=MATHESIS LAB');
    await expect(logo).toBeVisible();
  });

  test('should display page heading', async ({ page }) => {
    // 페이지 제목 확인
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
  });

  test('should display navigation links', async ({ page }) => {
    // 네비게이션 요소 확인
    const links = page.locator('a');
    const count = await links.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display header buttons', async ({ page }) => {
    // 버튼 요소 확인
    const buttons = page.locator('button');
    const count = await buttons.count();
    expect(count).toBeGreaterThan(0);
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
