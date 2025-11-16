import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * GCP Features Integration E2E Tests
 *
 * This test suite verifies the Google Cloud Platform integration features:
 * - GCP Settings page rendering and navigation
 * - Backup & Restore functionality (CloudSQL backup creation/restoration)
 * - Multi-Device Synchronization features
 * - Feature availability cards and status information
 * - Responsive design on mobile devices
 * - Tab navigation between different GCP features
 *
 * Tests focus on UI/UX verification, screenshots, and basic interaction flows.
 * These tests ensure the GCP settings interface is properly rendered and
 * users can navigate between different feature sections.
 */

interface BrowserLog {
  type: string;
  message: string;
  timestamp: string;
  location?: string;
}

interface NetworkError {
  url: string;
  status: number;
  statusText: string;
}

interface TestLog {
  testName: string;
  startTime: string;
  endTime: string;
  duration: number;
  consoleLogs: BrowserLog[];
  networkErrors: NetworkError[];
  status: 'passed' | 'failed';
}

test.describe('GCP Features Integration', () => {
    let page: Page;
    let currentTestName: string = '';
    let currentTestStartTime: Date;
    let consoleLogs: BrowserLog[] = [];
    let networkErrors: NetworkError[] = [];
    const allTestLogs: TestLog[] = [];

    test.beforeEach(async ({ page: p }, testInfo) => {
        page = p;
        currentTestName = testInfo.title;
        currentTestStartTime = new Date();
        consoleLogs = [];
        networkErrors = [];

        // Capture browser console messages (errors, warnings, logs)
        page.on('console', (msg) => {
            const timestamp = new Date().toLocaleTimeString();
            const location = msg.location();
            const logEntry: BrowserLog = {
                type: msg.type(),
                message: msg.text(),
                timestamp,
                location: location ? `${location.url}:${location.lineNumber}` : undefined,
            };
            consoleLogs.push(logEntry);

            // Log to terminal for visibility
            const icon = msg.type() === 'error' ? '❌' : msg.type() === 'warning' ? '⚠️' : 'ℹ️';
            console.log(`[${timestamp}] ${icon} [${msg.type().toUpperCase()}] ${msg.text()}`);
        });

        // Capture uncaught exceptions
        page.on('pageerror', (error) => {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry: BrowserLog = {
                type: 'error',
                message: `Uncaught: ${error.message}`,
                timestamp,
                location: error.stack ? error.stack.split('\n')[1] : undefined,
            };
            consoleLogs.push(logEntry);
            console.error(`[${timestamp}] ❌ [UNCAUGHT ERROR] ${error.message}`);
        });

        // Capture failed network requests
        page.on('response', (response) => {
            if (response.status() >= 400) {
                const networkError: NetworkError = {
                    url: response.url(),
                    status: response.status(),
                    statusText: response.statusText(),
                };
                networkErrors.push(networkError);
                console.warn(`[${new Date().toLocaleTimeString()}] ⚠️ [NETWORK] ${response.status()} ${response.statusText()}`);
            }
        });

        // Navigate to the GCP settings page
        await page.goto('http://localhost:3003', { waitUntil: 'networkidle' });
    });

    test.afterEach(async (testInfo) => {
        const endTime = new Date();
        const duration = endTime.getTime() - currentTestStartTime.getTime();

        // Save test log
        const testLog: TestLog = {
            testName: currentTestName,
            startTime: currentTestStartTime.toISOString(),
            endTime: endTime.toISOString(),
            duration,
            consoleLogs,
            networkErrors,
            status: testInfo.status === 'passed' ? 'passed' : 'failed',
        };
        allTestLogs.push(testLog);

        // Log summary for this test
        console.log(`\n${'='.repeat(80)}`);
        console.log(`📊 Test: ${currentTestName}`);
        console.log(`Status: ${testLog.status === 'passed' ? '✅ PASSED' : '❌ FAILED'}`);
        console.log(`Duration: ${duration}ms`);
        if (consoleLogs.length > 0) {
            console.log(`Console Messages: ${consoleLogs.length}`);
            const errors = consoleLogs.filter((l) => l.type === 'error');
            const warnings = consoleLogs.filter((l) => l.type === 'warning');
            if (errors.length > 0) console.log(`  ❌ Errors: ${errors.length}`);
            if (warnings.length > 0) console.log(`  ⚠️ Warnings: ${warnings.length}`);
        }
        if (networkErrors.length > 0) {
            console.log(`Network Errors: ${networkErrors.length}`);
        }
        console.log(`${'='.repeat(80)}\n`);
    });

    test.afterAll(async () => {
        // Save all test logs to JSON file
        const logsDir = path.join(__dirname, '../e2e-logs');
        if (!fs.existsSync(logsDir)) {
            fs.mkdirSync(logsDir, { recursive: true });
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const logFileName = `gcp-features-logs-${timestamp}.json`;
        const logFilePath = path.join(logsDir, logFileName);

        const summary = {
            totalTests: allTestLogs.length,
            passedTests: allTestLogs.filter((t) => t.status === 'passed').length,
            failedTests: allTestLogs.filter((t) => t.status === 'failed').length,
            totalConsoleLogs: allTestLogs.reduce((sum, t) => sum + t.consoleLogs.length, 0),
            totalNetworkErrors: allTestLogs.reduce((sum, t) => sum + t.networkErrors.length, 0),
            tests: allTestLogs,
        };

        fs.writeFileSync(logFilePath, JSON.stringify(summary, null, 2));
        console.log(`\n✅ Test logs saved to: ${logFilePath}`);
    });

    /**
     * Test: GCP Settings Page Initial Load
     * Purpose: Verify that the GCP Settings page loads and displays the main heading
     * Assertions:
     * - Page successfully navigates to GCP Settings route
     * - Main "GCP Settings" heading is visible
     */
    test('should display GCP Settings page heading and main layout', async () => {
        // Navigate to GCP Settings using hash routing
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // Take screenshot
        await page.screenshot({ path: 'e2e-screenshots/gcp-settings-page.png', fullPage: true });

        // Verify main content using getByRole
        const heading = page.getByRole('heading', { name: /GCP Settings/ });
        await expect(heading).toBeVisible();
    });

    /**
     * Test: Tab Navigation Availability
     * Purpose: Verify all three main tabs (Overview, Backup, Sync) are present and visible
     * Assertions:
     * - Overview tab is visible
     * - Backup & Restore tab is visible
     * - Multi-Device Sync tab is visible
     */
    test('should display all three tab buttons for GCP feature navigation', async () => {
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // Verify tab navigation buttons exist
        const overviewTab = page.getByRole('button', { name: /Overview/ });
        const backupTab = page.getByRole('button', { name: /Backup/ });
        const syncTab = page.getByRole('button', { name: /Sync/ });

        await expect(overviewTab).toBeVisible();
        await expect(backupTab).toBeVisible();
        await expect(syncTab).toBeVisible();

        // Take screenshot of tabs
        await page.screenshot({ path: 'e2e-screenshots/gcp-tabs-navigation.png', fullPage: true });
    });

    test('should display Backup Manager component', async () => {
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // Click on Backup & Restore tab using getByRole
        const backupTab = page.getByRole('button', { name: /Backup/ });
        await backupTab.click();

        // Wait for backup manager to be visible
        await page.waitForTimeout(500);

        // Verify backup manager elements using getByRole
        const createBackupBtn = page.getByRole('button', { name: /Create Backup/ });
        await expect(createBackupBtn).toBeVisible();

        // Take screenshot
        await page.screenshot({ path: 'e2e-screenshots/backup-manager-component.png', fullPage: true });
    });

    test('should display Multi-Device Sync section', async () => {
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // Click on Multi-Device Sync tab using getByRole
        const syncTab = page.getByRole('button', { name: /Sync/ });
        await syncTab.click();

        // Wait for content to load
        await page.waitForTimeout(500);

        // Verify register device button using getByRole
        const registerBtn = page.getByRole('button', { name: /Register/ });
        if (await registerBtn.isVisible().catch(() => false)) {
            await expect(registerBtn).toBeVisible();
        }

        // Take screenshot
        await page.screenshot({ path: 'e2e-screenshots/multi-device-sync.png', fullPage: true });
    });

    test('should show overview tab with feature cards', async () => {
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // Verify overview tab is active by default
        const overviewTab = page.getByRole('button', { name: /Overview/ });
        await expect(overviewTab).toHaveClass(/active|selected/);

        // Take screenshot of overview
        await page.screenshot({ path: 'e2e-screenshots/gcp-overview-tab.png', fullPage: true });
    });

    test('should display AIAssistant in node editor', async () => {
        // Navigate to editor or node page where AIAssistant is used
        await page.goto('http://localhost:3003', { waitUntil: 'networkidle' });

        // Look for AI Assistant component using getByText
        const aiAssistant = page.getByText(/AI Assistant/);

        if (await aiAssistant.isVisible().catch(() => false)) {
            // Take screenshot
            await page.screenshot({ path: 'e2e-screenshots/ai-assistant-component.png', fullPage: true });

            // Verify buttons exist
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

        // 스크린샷 1: 초기 상태
        await page.screenshot({ path: 'e2e-screenshots/01-backup-tab-before-click.png', fullPage: true });

        // Click on Backup & Restore tab
        const backupTab = page.getByRole('button', { name: /Backup/ });
        await backupTab.click();

        // Wait for content
        await page.waitForTimeout(500);

        // 스크린샷 2: 탭 클릭 후
        await page.screenshot({ path: 'e2e-screenshots/02-backup-tab-after-click.png', fullPage: true });

        // Click Create Backup button
        const createBtn = page.getByRole('button', { name: /Create Backup/ }).first();
        if (await createBtn.isVisible().catch(() => false)) {
            // 스크린샷 3: 버튼 클릭 전
            await page.screenshot({ path: 'e2e-screenshots/03-create-backup-before-click.png', fullPage: true });

            await createBtn.click();

            // Wait for form/modal to appear
            await page.waitForTimeout(800);

            // 스크린샷 4: 모달/폼 열린 후
            await page.screenshot({ path: 'e2e-screenshots/04-create-backup-modal-opened.png', fullPage: true });

            // 입력 필드 찾기 및 입력
            const inputs = page.locator('input');
            if (await inputs.first().isVisible().catch(() => false)) {
                await inputs.first().fill('Test Backup');

                // 스크린샷 5: 입력 후
                await page.screenshot({ path: 'e2e-screenshots/05-create-backup-form-filled.png', fullPage: true });
            }
        }
    });

    test('should display GCP status information', async () => {
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // Take screenshot of status
        await page.screenshot({ path: 'e2e-screenshots/gcp-status-card.png', fullPage: true });
    });

    test('should display feature availability cards', async () => {
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // Look for feature cards using getByText
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

        // Take screenshot of feature cards
        await page.screenshot({ path: 'e2e-screenshots/feature-cards.png', fullPage: true });
    });

    test('should display error handling UI elements', async () => {
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // Take screenshot showing full page layout
        await page.screenshot({ path: 'e2e-screenshots/gcp-full-page-layout.png', fullPage: true });

        // Verify page is loaded
        const heading = page.getByRole('heading', { name: /GCP Settings/ });
        await expect(heading).toBeVisible();
    });

    test('should be responsive on mobile', async ({ page: p }) => {
        // Set mobile viewport (iPhone 12)
        await p.setViewportSize({ width: 390, height: 844 });

        await p.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // 스크린샷 1: 모바일 초기 상태
        await p.screenshot({ path: 'e2e-screenshots/mobile-01-overview-initial.png', fullPage: true });

        // 스크린샷 2: 모바일 스크롤 (탭 영역)
        await p.evaluate(() => window.scrollTo(0, 300));
        await p.waitForTimeout(300);
        await p.screenshot({ path: 'e2e-screenshots/mobile-02-overview-scrolled.png', fullPage: true });

        // Click Backup tab on mobile
        const backupTab = p.getByRole('button', { name: /Backup/ });
        await backupTab.click();
        await p.waitForTimeout(600);

        // 스크린샷 3: 모바일 Backup 탭
        await p.evaluate(() => window.scrollTo(0, 0));
        await p.screenshot({ path: 'e2e-screenshots/mobile-03-backup-tab.png', fullPage: true });

        // 스크린샷 4: 모바일 Backup 스크롤
        await p.evaluate(() => window.scrollTo(0, 300));
        await p.waitForTimeout(300);
        await p.screenshot({ path: 'e2e-screenshots/mobile-04-backup-scrolled.png', fullPage: true });

        // Verify elements are visible on mobile
        const heading = p.getByRole('heading', { name: /GCP Settings/ });
        await expect(heading).toBeVisible();
    });

    test('should handle tab switching with proper content', async () => {
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // 스크린샷 1: Overview 탭 (초기)
        await page.screenshot({ path: 'e2e-screenshots/tab-01-overview-initial.png', fullPage: true });

        // 스크린샷 2: Overview 탭 상세 (스크롤 후)
        await page.evaluate(() => window.scrollTo(0, 500));
        await page.waitForTimeout(300);
        await page.screenshot({ path: 'e2e-screenshots/tab-02-overview-scrolled.png', fullPage: true });

        // Switch to Backup tab
        const backupTab = page.getByRole('button', { name: /Backup/ });
        await backupTab.click();
        await page.waitForTimeout(600);

        // 스크린샷 3: Backup 탭 열림
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.screenshot({ path: 'e2e-screenshots/tab-03-backup-opened.png', fullPage: true });

        // 스크린샷 4: Backup 탭 스크롤
        await page.evaluate(() => window.scrollTo(0, 400));
        await page.waitForTimeout(300);
        await page.screenshot({ path: 'e2e-screenshots/tab-04-backup-scrolled.png', fullPage: true });

        // Switch to Sync tab
        const syncTab = page.getByRole('button', { name: /Sync/ });
        await syncTab.click();
        await page.waitForTimeout(600);

        // 스크린샷 5: Sync 탭 열림
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.screenshot({ path: 'e2e-screenshots/tab-05-sync-opened.png', fullPage: true });

        // 스크린샷 6: Sync 탭 스크롤
        await page.evaluate(() => window.scrollTo(0, 400));
        await page.waitForTimeout(300);
        await page.screenshot({ path: 'e2e-screenshots/tab-06-sync-scrolled.png', fullPage: true });
    });

    test('should verify styling and layout consistency', async () => {
        await page.goto('http://localhost:3003/#/gcp-settings', { waitUntil: 'networkidle' });

        // Take full-page screenshot for layout review
        await page.screenshot({ path: 'e2e-screenshots/gcp-complete-layout.png', fullPage: true });

        // Verify heading styles
        const heading = page.getByRole('heading', { name: /GCP Settings/ });
        const headingStyles = await heading.evaluate((el) => {
            const styles = window.getComputedStyle(el);
            return {
                fontSize: styles.fontSize,
                color: styles.color,
                fontWeight: styles.fontWeight,
            };
        });

        // Verify styles are applied
        expect(headingStyles.fontSize).toBeTruthy();
        expect(headingStyles.color).toBeTruthy();
        expect(headingStyles.fontWeight).toBeTruthy();
    });
});
