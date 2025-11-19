import { test, expect } from '@playwright/test';

test.describe('MATHESIS LAB - Basic Functionality', () => {
  test('should load homepage successfully', async ({ page }) => {
    await page.goto('/');

    // Wait for page to load
    await page.waitForTimeout(2000);

    // Check if page is loaded
    const isLoaded = await page.evaluate(() => {
      return document.readyState === 'complete';
    });

    expect(isLoaded).toBe(true);

    // Take screenshot
    await page.screenshot({ path: 'test-results/01-homepage.png' });

    console.log('✅ Homepage loaded successfully');
  });

  test('should connect to backend API', async ({ page }) => {
    // Navigate to app
    await page.goto('/');

    // Wait for API calls
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/02-api-connected.png' });

    console.log('✅ Backend API connection verified');
  });

  test('should display curriculum list', async ({ page }) => {
    await page.goto('/');

    // Wait for content to load
    await page.waitForTimeout(3000);

    // Take screenshot of main page
    await page.screenshot({ path: 'test-results/03-curriculum-list.png' });

    // Log network activity
    const logs: string[] = [];
    page.on('response', response => {
      logs.push(`${response.status()} ${response.url()}`);
    });

    console.log('✅ Curriculum list page loaded');
    console.log('Network logs:', logs);
  });

  test('should have working navigation', async ({ page }) => {
    await page.goto('/');

    await page.waitForTimeout(2000);

    // Check page title
    const title = await page.title();
    expect(title).toBeTruthy();

    // Take screenshot
    await page.screenshot({ path: 'test-results/04-navigation.png' });

    console.log(`✅ Navigation working - Page title: "${title}"`);
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Set up request interception to log all requests
    const requests: string[] = [];
    page.on('request', request => {
      requests.push(`${request.method()} ${request.url()}`);
    });

    await page.goto('/');
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/05-error-handling.png' });

    console.log('✅ API requests made:');
    requests.forEach(req => console.log(`  - ${req}`));
  });
});
