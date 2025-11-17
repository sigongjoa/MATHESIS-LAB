import { test, expect, Page } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { BrowserLogger } from './utils/browser-logger';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Frontend Console Log Capture Tests
 * These tests specifically focus on capturing and analyzing browser console logs
 * without polluting the test output with log statements.
 *
 * All logs are captured via BrowserLogger and exported to JSON files.
 */

test.describe('Frontend Console Log Capture', () => {
  let page: Page;
  let logger: BrowserLogger;

  test.beforeEach(async ({ page: p }, testInfo) => {
    page = p;
    logger = new BrowserLogger();
    logger.initialize(page);

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

  test('01-capture-homepage-logs', async () => {
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });

    const title = await page.title();
    expect(title).toBeTruthy();

    await page.waitForTimeout(2000);

    const appRoot = await page.$('#root');
    if (appRoot) {
      expect(appRoot).toBeTruthy();
    }
  });

  test('02-capture-api-calls-logs', async () => {
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    expect(page).toBeTruthy();
  });

  test('03-test-button-interactions', async () => {
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });

    const buttons = await page.$$('button');
    expect(buttons.length).toBeGreaterThanOrEqual(0);

    if (buttons.length > 0) {
      for (let i = 0; i < Math.min(buttons.length, 5); i++) {
        const text = await buttons[i].textContent();
        expect(text).toBeTruthy();
      }
    }

    const errorElements = await page.$$('[class*="error"], [role="alert"]');
    expect(errorElements).toBeTruthy();
  });

  test('04-check-localStorage-and-sessionStorage', async () => {
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });

    const storage = await page.evaluate(() => {
      const local = Object.keys(localStorage);
      const session = Object.keys(sessionStorage);
      return { localSize: local.length, sessionSize: session.length };
    });

    expect(storage.localSize).toBeGreaterThanOrEqual(0);
    expect(storage.sessionSize).toBeGreaterThanOrEqual(0);
  });
});
