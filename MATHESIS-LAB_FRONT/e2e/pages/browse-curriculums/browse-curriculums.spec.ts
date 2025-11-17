import { test, expect } from '@playwright/test';
import { BROWSE_CURRICULUMS_CONFIG } from './config';

test.describe('Browse Curriculums Page', () => {
  test.beforeEach(async ({ page }) => {
    // 페이지 네비게이션
    await page.goto(BROWSE_CURRICULUMS_CONFIG.url, {
      waitUntil: 'networkidle',
      timeout: BROWSE_CURRICULUMS_CONFIG.timeouts.navigation,
    });
  });

  test('should display page heading', async ({ page }) => {
    // 페이지 제목 확인
    const heading = page.locator('p:has-text("모든 커리큘럼 둘러보기")');
    await expect(heading).toBeVisible();
  });

  test('should display curriculum cards', async ({ page }) => {
    // 카드 요소 확인
    const cards = page.locator('[class*="group"]');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display search input', async ({ page }) => {
    // 검색 입력 필드 확인
    const searchInput = page.locator('input[placeholder*="커리큘럼"]');
    await expect(searchInput).toBeVisible();
  });

  test('should display header navigation', async ({ page }) => {
    // MATHESIS LAB 로고
    const logo = page.locator('text=MATHESIS LAB');
    await expect(logo).toBeVisible();

    // 헤더 링크 (내 커리큘럼 또는 다른 네비게이션 요소)
    const headerLinks = page.locator('a[href*="curriculum"], a[href*="/"]');
    const count = await headerLinks.count();

    // 최소 하나의 네비게이션 링크가 있어야 함
    expect(count).toBeGreaterThan(0);
  });

  test('should have visible buttons', async ({ page }) => {
    // 버튼 요소 확인
    const buttons = page.locator('button');
    const count = await buttons.count();
    expect(count).toBeGreaterThan(0);

    // 첫 번째 버튼이 보이는지 확인
    const firstButton = buttons.first();
    await expect(firstButton).toBeVisible();
  });

  test('should not have critical console errors', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // 페이지가 완전히 로드될 때까지 대기
    await page.waitForLoadState('networkidle');

    // GSI 관련 에러는 무시 (개발 환경에서 발생)
    const criticalErrors = consoleErrors.filter((error) => {
      const ignorePatterns = [
        'GSI_LOGGER',
        'Origin is not allowed',
        'Provided button width',
        'cdn.tailwindcss.com',
      ];
      return !ignorePatterns.some((pattern) => error.includes(pattern));
    });

    // 심각한 에러가 없어야 함
    console.log('Console Errors:', criticalErrors);
    expect(criticalErrors.length).toBeLessThanOrEqual(0);
  });
});
