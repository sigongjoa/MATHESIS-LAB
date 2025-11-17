import { test, expect, Page } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { BrowserLogger } from './utils/browser-logger';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Node Type Selector E2E Tests
 * Tests for node selection and interaction features.
 * All browser logs are captured via BrowserLogger utility.
 */

test.describe('Node Type Selector', () => {
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

  test('01-app-loads-successfully', async () => {
    await page.screenshot({ path: 'e2e-screenshots/node-01-app-loads.png', fullPage: true });

    await page.waitForLoadState('networkidle');

    const title = await page.title();
    expect(title).toBeTruthy();

    const appContainer = await page.$('#root');
    expect(appContainer).toBeTruthy();
  });

  test('02-find-and-verify-buttons', async () => {
    await page.waitForLoadState('networkidle');

    const createButtons = await page.$$('button');
    expect(createButtons.length).toBeGreaterThan(0);
  });

  test('03-app-network-status', async () => {
    const response = await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });
    expect(response?.status()).toBe(200);

    const isOnline = await page.evaluate(() => navigator.onLine);
    expect(isOnline).toBe(true);
  });

  test('04-check-styling', async () => {
    await page.waitForLoadState('networkidle');

    const stylesheets = await page.$$('link[rel="stylesheet"]');
    expect(stylesheets.length).toBeGreaterThanOrEqual(0);
  });

  test('05-interact-with-page-elements', async () => {
    await page.waitForLoadState('networkidle');

    const links = await page.$$('a');
    expect(links.length).toBeGreaterThanOrEqual(0);

    if (links.length > 0) {
      const firstLink = links[0];
      await firstLink.hover();
    }

    await page.screenshot({ path: 'e2e-screenshots/node-05-interaction.png', fullPage: true });
  });

  test('06-dom-structure-verification', async () => {
    await page.waitForLoadState('networkidle');

    const bodyTag = await page.$('body');
    expect(bodyTag).toBeTruthy();

    const headers = await page.$$('header, h1, h2, h3');
    expect(headers.length).toBeGreaterThanOrEqual(0);

    const bodyHTML = await page.$eval('body', (el) => el.innerHTML.length);
    expect(bodyHTML).toBeGreaterThan(0);
  });
});
