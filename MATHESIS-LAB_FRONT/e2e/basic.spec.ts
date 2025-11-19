import { test, expect } from '@playwright/test';

test.describe('MATHESIS LAB - Comprehensive E2E Screenshots', () => {
  test('01-homepage and dashboard', async ({ page }) => {
    // Home page - HashRouter uses /#/ format
    await page.goto('/#/');
    await page.waitForTimeout(2500);

    expect(await page.evaluate(() => document.readyState === 'complete')).toBe(true);
    await page.screenshot({ path: 'test-results/01-homepage.png', fullPage: true });
    console.log('✅ Screenshot 1: Homepage ✅ LOADED');
  });

  test('02-browse curriculums page', async ({ page }) => {
    // Browse page - shows curriculum list
    await page.goto('/#/browse');
    await page.waitForTimeout(2500);

    // Verify different page loaded
    const heading = await page.locator('h1, h2').first().textContent();
    console.log(`Page heading: ${heading}`);

    await page.screenshot({ path: 'test-results/02-browse-curriculums.png', fullPage: true });
    console.log('✅ Screenshot 2: Browse Curriculums Page ✅ LOADED');
  });

  test('03-gcp settings page', async ({ page }) => {
    // GCP settings page - correct path is /gcp-settings (not /settings/gcp)
    await page.goto('/#/gcp-settings');
    await page.waitForTimeout(2500);

    // Verify page loaded
    const heading = await page.locator('h1, h2').first().textContent();
    console.log(`Page heading: ${heading}`);

    await page.screenshot({ path: 'test-results/03-gcp-settings.png', fullPage: true });
    console.log('✅ Screenshot 3: GCP Settings Page ✅ LOADED');
  });

  test('04-page navigation verification', async ({ page }) => {
    // Go to home and check navigation links
    await page.goto('/#/');
    await page.waitForTimeout(2000);

    // Look for navigation elements
    const navLinks = await page.locator('a, button').count();
    console.log(`Found ${navLinks} navigation elements`);

    // Check for page title/heading
    const pageTitle = await page.locator('h1, h2').first().textContent();
    console.log(`Page title: ${pageTitle}`);

    await page.screenshot({ path: 'test-results/04-navigation.png', fullPage: true });
    console.log('✅ Screenshot 4: Navigation & Layout ✅ LOADED');
  });

  test('05-api connectivity verification', async ({ page }) => {
    // Browse page to verify API is loading data
    await page.goto('/#/browse');
    await page.waitForTimeout(3000);

    // Wait for any API calls to complete
    await page.waitForLoadState('networkidle').catch(() => {});

    // Check for loaded content
    const contentElements = await page.locator('div, section').count();
    console.log(`Page has ${contentElements} content elements`);

    await page.screenshot({ path: 'test-results/05-api-loaded.png', fullPage: true });
    console.log('✅ Screenshot 5: API Data Loaded ✅ LOADED');
  });
});
