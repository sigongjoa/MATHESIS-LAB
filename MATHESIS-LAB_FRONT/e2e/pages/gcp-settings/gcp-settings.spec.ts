import { test, expect } from '@playwright/test';
import { GCP_SETTINGS_CONFIG } from './config';

test.describe('GCP Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    // 페이지 네비게이션
    await page.goto(GCP_SETTINGS_CONFIG.url, {
      waitUntil: 'networkidle',
      timeout: GCP_SETTINGS_CONFIG.timeouts.navigation,
    });
  });

  test('should display GCP Settings page heading and main layout', async ({ page }) => {
    // 제목 확인
    const heading = page.locator(GCP_SETTINGS_CONFIG.selectors.heading);
    await expect(heading).toBeVisible();

    // 부제목 확인
    const subtitle = page.locator(GCP_SETTINGS_CONFIG.selectors.subtitle);
    await expect(subtitle).toBeVisible();
  });

  test('should display tab buttons', async ({ page }) => {
    // Overview 탭
    const overviewTab = page.locator(GCP_SETTINGS_CONFIG.selectors.tabs.overview);
    await expect(overviewTab).toBeVisible();

    // Backup & Restore 탭
    const backupTab = page.locator(GCP_SETTINGS_CONFIG.selectors.tabs.backup);
    await expect(backupTab).toBeVisible();

    // Multi-Device Sync 탭
    const syncTab = page.locator(GCP_SETTINGS_CONFIG.selectors.tabs.sync);
    await expect(syncTab).toBeVisible();
  });

  test('should display GCP Integration Status section', async ({ page }) => {
    const statusHeading = page.locator(GCP_SETTINGS_CONFIG.selectors.statusHeading);
    await expect(statusHeading).toBeVisible();

    const statusCard = page.locator(GCP_SETTINGS_CONFIG.selectors.statusCard);
    await expect(statusCard).toBeVisible();
  });

  test('should display Available Features section', async ({ page }) => {
    const featuresHeading = page.locator(GCP_SETTINGS_CONFIG.selectors.featuresHeading);
    await expect(featuresHeading).toBeVisible();

    // 기능 카드 확인
    const featureCards = page.locator(GCP_SETTINGS_CONFIG.selectors.featureCards);
    const count = await featureCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display action buttons', async ({ page }) => {
    // Refresh Status 버튼
    const refreshButton = page.locator(GCP_SETTINGS_CONFIG.selectors.buttons.refresh);
    await expect(refreshButton).toBeVisible();

    // Health Check 버튼
    const healthCheckButton = page.locator(GCP_SETTINGS_CONFIG.selectors.buttons.healthCheck);
    await expect(healthCheckButton).toBeVisible();
  });

  test('should have no console errors', async ({ page }) => {
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

  test('should switch between tabs', async ({ page }) => {
    // Overview 탭이 기본으로 활성화됨
    let activeTab = page.locator(GCP_SETTINGS_CONFIG.selectors.tabs.overview + '[class*="active"]');
    await expect(activeTab).toBeVisible();

    // Backup 탭으로 전환
    await page.locator(GCP_SETTINGS_CONFIG.selectors.tabs.backup).click();
    activeTab = page.locator(GCP_SETTINGS_CONFIG.selectors.tabs.backup + '[class*="active"]');
    await expect(activeTab).toBeVisible();

    // Multi-Device Sync 탭으로 전환
    await page.locator(GCP_SETTINGS_CONFIG.selectors.tabs.sync).click();
    activeTab = page.locator(GCP_SETTINGS_CONFIG.selectors.tabs.sync + '[class*="active"]');
    await expect(activeTab).toBeVisible();
  });
});
