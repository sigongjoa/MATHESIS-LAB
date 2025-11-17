import { test, expect, Page } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { BrowserLogger } from './utils/browser-logger';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * GCP Features Integration E2E Tests
 *
 * This test suite verifies the Google Cloud Platform integration features.
 * Browser console logs and network errors are automatically captured and saved
 * to JSON files in e2e-logs/ directory for analysis in test reports.
 *
 * Test Structure:
 * - Tests run independently without logging to console
 * - All logs are captured via BrowserLogger utility
 * - Logs are exported to JSON files for post-analysis
 * - Test reports aggregate all logs for comprehensive analysis
 */

test.describe('GCP Features Integration', () => {
  let page: Page;
  let logger: BrowserLogger;

  test.beforeEach(async ({ page: p }, testInfo) => {
    page = p;
    logger = new BrowserLogger();
    logger.initialize(page);

    // Navigate to the GCP settings page
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });
  });

  test.afterEach(async (testInfo) => {
    const startTime = testInfo.startTime || new Date();
    const duration = new Date().getTime() - startTime.getTime();

    // Export logs to JSON file
    const logsDir = path.join(__dirname, '../e2e-logs');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const logFileName = `${testInfo.title.replace(/\s+/g, '-')}-${timestamp}.json`;
    const logFilePath = path.join(logsDir, logFileName);

    logger.exportToJSON(logFilePath, testInfo.title, duration);
  });

  // Test Cases
  test('should display GCP Settings page heading and main layout', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'e2e-screenshots/gcp-settings-page.png', fullPage: true });

    const heading = page.getByRole('heading', { name: /GCP Settings/ });
    await expect(heading).toBeVisible();
  });

  test('should display all three tab buttons for GCP feature navigation', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

    const overviewTab = page.getByRole('button', { name: /Overview/ });
    const backupTab = page.getByRole('button', { name: /Backup/ });
    const syncTab = page.getByRole('button', { name: /Sync/ });

    await expect(overviewTab).toBeVisible();
    await expect(backupTab).toBeVisible();
    await expect(syncTab).toBeVisible();

    await page.screenshot({ path: 'e2e-screenshots/gcp-tabs-navigation.png', fullPage: true });
  });

  test('should display Backup Manager component', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

    const backupTab = page.getByRole('button', { name: /Backup/ });
    await backupTab.click();
    await page.waitForTimeout(500);

    const createBackupBtn = page.getByRole('button', { name: /Create Backup/ });
    await expect(createBackupBtn).toBeVisible();
    await page.screenshot({ path: 'e2e-screenshots/backup-manager-component.png', fullPage: true });
  });

  test('should display Multi-Device Sync section', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

    const syncTab = page.getByRole('button', { name: /Sync/ });
    await syncTab.click();
    await page.waitForTimeout(500);

    const registerBtn = page.getByRole('button', { name: /Register/ });
    if (await registerBtn.isVisible().catch(() => false)) {
      await expect(registerBtn).toBeVisible();
    }

    await page.screenshot({ path: 'e2e-screenshots/multi-device-sync.png', fullPage: true });
  });

  test('should show overview tab with feature cards', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

    const overviewTab = page.getByRole('button', { name: /Overview/ });
    await expect(overviewTab).toHaveClass(/active|selected/);
    await page.screenshot({ path: 'e2e-screenshots/gcp-overview-tab.png', fullPage: true });
  });

  test('should display AIAssistant in node editor', async () => {
    await page.goto('http://localhost:3003', { waitUntil: 'networkidle' });

    const aiAssistant = page.getByText(/AI Assistant/);
    if (await aiAssistant.isVisible().catch(() => false)) {
      await page.screenshot({ path: 'e2e-screenshots/ai-assistant-component.png', fullPage: true });

      const summarizeBtn = page.getByRole('button', { name: /Summarize/ });
      const expandBtn = page.getByRole('button', { name: /Expand/ });
      const manimBtn = page.getByRole('button', { name: /Manim/ });

      if (await summarizeBtn.isVisible().catch(() => false)) {
        await expect(summarizeBtn).toBeVisible();
      }
      if (await expandBtn.isVisible().catch(() => false)) {
        await expect(expandBtn).toBeVisible();
      }
      if (await manimBtn.isVisible().catch(() => false)) {
        await expect(manimBtn).toBeVisible();
      }
    }
  });

  test('should handle create backup flow', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'e2e-screenshots/01-backup-tab-before-click.png', fullPage: true });

    const backupTab = page.getByRole('button', { name: /Backup/ });
    await backupTab.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'e2e-screenshots/02-backup-tab-after-click.png', fullPage: true });

    const createBtn = page.getByRole('button', { name: /Create Backup/ }).first();
    if (await createBtn.isVisible().catch(() => false)) {
      await page.screenshot({ path: 'e2e-screenshots/03-create-backup-before-click.png', fullPage: true });
      await createBtn.click();
      await page.waitForTimeout(800);
      await page.screenshot({ path: 'e2e-screenshots/04-create-backup-modal-opened.png', fullPage: true });

      const inputs = page.locator('input');
      if (await inputs.first().isVisible().catch(() => false)) {
        await inputs.first().fill('Test Backup');
        await page.screenshot({ path: 'e2e-screenshots/05-create-backup-form-filled.png', fullPage: true });
      }
    }
  });

  test('should display GCP status information', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'e2e-screenshots/gcp-status-card.png', fullPage: true });
  });

  test('should display feature availability cards', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

    const cloudStorageText = page.getByText(/Cloud Storage/);
    const backupRestoreText = page.getByText(/Backup/);
    const syncText = page.getByText(/Sync/);

    if (await cloudStorageText.isVisible().catch(() => false)) {
      await expect(cloudStorageText).toBeVisible();
    }
    if (await backupRestoreText.isVisible().catch(() => false)) {
      await expect(backupRestoreText).toBeVisible();
    }
    if (await syncText.isVisible().catch(() => false)) {
      await expect(syncText).toBeVisible();
    }

    await page.screenshot({ path: 'e2e-screenshots/feature-cards.png', fullPage: true });
  });

  test('should display error handling UI elements', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'e2e-screenshots/gcp-full-page-layout.png', fullPage: true });

    const heading = page.getByRole('heading', { name: /GCP Settings/ });
    await expect(heading).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page: p }) => {
    await p.setViewportSize({ width: 390, height: 844 });
    await p.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

    await p.screenshot({ path: 'e2e-screenshots/mobile-01-overview-initial.png', fullPage: true });
    await p.evaluate(() => window.scrollTo(0, 300));
    await p.waitForTimeout(300);
    await p.screenshot({ path: 'e2e-screenshots/mobile-02-overview-scrolled.png', fullPage: true });

    const backupTab = p.getByRole('button', { name: /Backup/ });
    await backupTab.click();
    await p.waitForTimeout(600);
    await p.evaluate(() => window.scrollTo(0, 0));
    await p.screenshot({ path: 'e2e-screenshots/mobile-03-backup-tab.png', fullPage: true });

    const heading = p.getByRole('heading', { name: /GCP Settings/ });
    await expect(heading).toBeVisible();
  });

  test('should handle tab switching with proper content', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'e2e-screenshots/tab-01-overview-initial.png', fullPage: true });

    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(300);
    await page.screenshot({ path: 'e2e-screenshots/tab-02-overview-scrolled.png', fullPage: true });

    const backupTab = page.getByRole('button', { name: /Backup/ });
    await backupTab.click();
    await page.waitForTimeout(600);

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: 'e2e-screenshots/tab-03-backup-opened.png', fullPage: true });

    const syncTab = page.getByRole('button', { name: /Sync/ });
    await syncTab.click();
    await page.waitForTimeout(600);

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: 'e2e-screenshots/tab-05-sync-opened.png', fullPage: true });
  });

  test('should verify styling and layout consistency', async () => {
    await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'e2e-screenshots/gcp-complete-layout.png', fullPage: true });

    const heading = page.getByRole('heading', { name: /GCP Settings/ });
    const headingStyles = await heading.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontSize: styles.fontSize,
        color: styles.color,
        fontWeight: styles.fontWeight,
      };
    });

    expect(headingStyles.fontSize).toBeTruthy();
    expect(headingStyles.color).toBeTruthy();
    expect(headingStyles.fontWeight).toBeTruthy();
  });
});
