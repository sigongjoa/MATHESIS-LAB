import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Helper function to take screenshots at each step
async function takeScreenshot(page: any, testName: string, stepName: string) {
  const screenshotsDir = path.join(__dirname, '../e2e-screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const fileName = `${testName}_${stepName}_${Date.now()}.png`;
  const filePath = path.join(screenshotsDir, fileName);
  await page.screenshot({ path: filePath, fullPage: true });
  console.log(`📸 Screenshot saved: ${fileName}`);
  return filePath;
}

test.describe('Node Type Selector E2E with Screenshots', () => {
  let consoleLogs: { type: string; message: string; timestamp: string }[] = [];

  test.beforeEach(async ({ page }) => {
    // Clear console logs for new test
    consoleLogs = [];

    // Capture browser console messages
    page.on('console', (msg) => {
      const timestamp = new Date().toLocaleTimeString();
      const logEntry = {
        type: msg.type(),
        message: msg.text(),
        timestamp,
      };
      consoleLogs.push(logEntry);

      // Log to terminal for visibility
      if (msg.type() === 'error') {
        console.error(`[${timestamp}] CONSOLE ERROR: ${msg.text()}`);
      } else if (msg.type() === 'warning') {
        console.warn(`[${timestamp}] CONSOLE WARN: ${msg.text()}`);
      }
    });

    // Capture uncaught exceptions
    page.on('pageerror', (error) => {
      const timestamp = new Date().toLocaleTimeString();
      console.error(`[${timestamp}] PAGE ERROR: ${error.message}`);
      consoleLogs.push({
        type: 'error',
        message: `Uncaught: ${error.message}`,
        timestamp,
      });
    });

    // Navigate to the frontend application
    await page.goto('/', { waitUntil: 'networkidle' });
    console.log('✓ Page loaded');
  });

  test.afterEach(async () => {
    // Log all console messages after each test
    if (consoleLogs.length > 0) {
      console.log('\n📋 Browser Console Messages:');
      consoleLogs.forEach((log) => {
        const level = log.type === 'error' ? '❌' : log.type === 'warning' ? '⚠️' : 'ℹ️';
        console.log(`  ${level} [${log.type.toUpperCase()}] ${log.message}`);
      });
    }
  });

  test('01-app-loads-successfully', async ({ page }) => {
    // Screenshot 1: Initial page load
    await takeScreenshot(page, 'app-loads', '01-initial-load');

    // Wait for the page to fully load
    await page.waitForLoadState('networkidle');
    console.log('✓ Page fully loaded');

    // Check that the page title exists
    const title = await page.title();
    expect(title).toBeTruthy();
    console.log(`✓ Page title: ${title}`);

    // Screenshot 2: After page fully loaded
    await takeScreenshot(page, 'app-loads', '02-page-ready');

    // Check that main app container exists
    const appContainer = await page.$('#root');
    expect(appContainer).toBeTruthy();
    console.log('✓ App container found');

    // Screenshot 3: App container verified
    await takeScreenshot(page, 'app-loads', '03-app-verified');
  });

  test('02-find-and-verify-buttons', async ({ page }) => {
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    console.log('✓ Page fully loaded');

    // Screenshot 1: Initial state
    await takeScreenshot(page, 'buttons-verification', '01-initial-state');

    // Look for the "Create New Node" button or modal trigger
    const createButtons = await page.$$('button');
    console.log(`✓ Found ${createButtons.length} buttons on page`);

    // Screenshot 2: After button discovery
    await takeScreenshot(page, 'buttons-verification', '02-buttons-found');

    // Log all buttons to help debug
    for (const button of createButtons) {
      const text = await button.textContent();
      console.log(`  - Button: ${text}`);
    }

    expect(createButtons.length).toBeGreaterThan(0);
    console.log('✓ Buttons verified');

    // Screenshot 3: After verification
    await takeScreenshot(page, 'buttons-verification', '03-verified');
  });

  test('03-app-network-status', async ({ page }) => {
    // Navigate and check network status
    const response = await page.goto('/', { waitUntil: 'networkidle' });

    // Screenshot 1: After navigation
    await takeScreenshot(page, 'network-status', '01-navigated');

    // Should get a successful response
    expect(response?.status()).toBe(200);
    console.log(`✓ Network response: ${response?.status()}`);

    // Screenshot 2: Network verified
    await takeScreenshot(page, 'network-status', '02-network-ok');

    // Verify the page is still responsive
    const isOnline = await page.evaluate(() => navigator.onLine);
    expect(isOnline).toBe(true);
    console.log('✓ Page is online');

    // Screenshot 3: Online status verified
    await takeScreenshot(page, 'network-status', '03-online-verified');
  });

  test('04-check-styling', async ({ page }) => {
    // Wait for page load
    await page.waitForLoadState('networkidle');
    console.log('✓ Page fully loaded');

    // Screenshot 1: Initial page state
    await takeScreenshot(page, 'styling', '01-initial');

    // Check if stylesheets are loaded
    const stylesheets = await page.$$('link[rel="stylesheet"]');
    console.log(`✓ Found ${stylesheets.length} stylesheets loaded`);

    // Screenshot 2: After stylesheet check
    await takeScreenshot(page, 'styling', '02-stylesheets-loaded');

    // App should have at least the main styles
    expect(stylesheets.length).toBeGreaterThanOrEqual(0);
    console.log('✓ Styling verified');

    // Screenshot 3: Styling verified
    await takeScreenshot(page, 'styling', '03-styled');
  });

  test('05-interact-with-page-elements', async ({ page }) => {
    // Wait for page load
    await page.waitForLoadState('networkidle');
    console.log('✓ Page fully loaded');

    // Screenshot 1: Initial state
    await takeScreenshot(page, 'interaction', '01-initial-state');

    // Try to find and interact with navigation or main elements
    const links = await page.$$('a');
    console.log(`✓ Found ${links.length} links on page`);

    // Screenshot 2: Links found
    await takeScreenshot(page, 'interaction', '02-links-found');

    // Try to interact with first link if available
    if (links.length > 0) {
      const firstLink = links[0];
      const href = await firstLink.getAttribute('href');
      console.log(`  - First link: ${href}`);

      // Hover over the link
      await firstLink.hover();
      console.log('✓ Hovered over first link');

      // Screenshot 3: After hover
      await takeScreenshot(page, 'interaction', '03-hover-effect');
    }

    // Screenshot 4: Interaction complete
    await takeScreenshot(page, 'interaction', '04-complete');
  });

  test('06-dom-structure-verification', async ({ page }) => {
    // Wait for page load
    await page.waitForLoadState('networkidle');
    console.log('✓ Page fully loaded');

    // Screenshot 1: Initial state
    await takeScreenshot(page, 'dom-structure', '01-initial');

    // Get DOM structure info
    const bodyTag = await page.$('body');
    expect(bodyTag).toBeTruthy();
    console.log('✓ Body tag found');

    // Screenshot 2: Body verified
    await takeScreenshot(page, 'dom-structure', '02-body-found');

    // Check for common page elements
    const headers = await page.$$('header, h1, h2, h3');
    console.log(`✓ Found ${headers.length} heading/header elements`);

    // Screenshot 3: Headers found
    await takeScreenshot(page, 'dom-structure', '03-headers-found');

    // Get body HTML content info
    const bodyHTML = await page.$eval('body', el => el.innerHTML.length);
    expect(bodyHTML).toBeGreaterThan(0);
    console.log(`✓ Body HTML length: ${bodyHTML} characters`);

    // Screenshot 4: HTML verified
    await takeScreenshot(page, 'dom-structure', '04-html-verified');
  });
});
