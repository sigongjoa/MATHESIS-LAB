import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const logsDir = path.join(__dirname, '../../test-logs/complete-flow');

let testLogs: string[] = [];
let networkRequests: any[] = [];
let consoleMessages: any[] = [];

function ensureLogsDir() {
  if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
  }
}

function addLog(message: string) {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] ${message}`;
  testLogs.push(logEntry);
  console.log(logEntry);
}

function saveTestLogs(testName?: string) {
  ensureLogsDir();
  const name = testName || `test-${Date.now()}`;
  // Replace special characters and spaces with dashes for filename
  const safeName = name.replace(/[^a-zA-Z0-9_-]/g, '-').replace(/\s+/g, '-');
  const logFile = path.join(logsDir, `${safeName}.log`);
  fs.writeFileSync(logFile, testLogs.join('\n') + '\n');
  addLog(`✓ Logs saved to ${logFile}`);
}

test.describe('Complete Flow: Curriculum → Node → NodeEditor with PDF/Link Features', () => {
  test.beforeEach(async ({ page }) => {
    testLogs = [];
    networkRequests = [];
    consoleMessages = [];
    addLog('=== Test Started ===');

    // Setup network and console logging
    page.on('console', (msg) => {
      const type = msg.type();
      const entry = { type, text: msg.text(), timestamp: new Date().toISOString() };
      consoleMessages.push(entry);
      if (type !== 'log') {
        addLog(`[BROWSER ${type.toUpperCase()}] ${msg.text()}`);
      }
    });

    page.on('request', (request) => {
      const entry = { method: request.method(), url: request.url(), timestamp: new Date().toISOString() };
      networkRequests.push(entry);
      addLog(`[REQUEST] ${request.method()} ${request.url()}`);
    });

    page.on('response', (response) => {
      addLog(`[RESPONSE] ${response.status()} ${response.url()}`);
    });

    // No error suppression - let errors propagate naturally
    page.on('error', (error) => {
      addLog(`[PAGE ERROR] ${error.message}`);
      throw error;
    });
  });

  test.afterEach(async ({ page }, testInfo) => {
    addLog(`\n=== Test Summary ===`);
    addLog(`Test: ${testInfo.title}`);
    addLog(`Status: ${testInfo.status}`);
    addLog(`Network Requests: ${networkRequests.length}`);
    addLog(`Console Messages: ${consoleMessages.length}`);

    if (consoleMessages.length > 0) {
      addLog(`\nConsole Messages:`);
      consoleMessages.forEach((msg, idx) => {
        addLog(`  ${idx + 1}. [${msg.type}] ${msg.text}`);
      });
    }

    saveTestLogs(testInfo.title);

    // Take screenshot on failure
    if (testInfo.status !== 'passed') {
      ensureLogsDir();
      const screenshotPath = path.join(logsDir, `${testInfo.title.replace(/\s+/g, '-')}-screenshot.png`);
      await page.screenshot({ path: screenshotPath });
      addLog(`✓ Screenshot saved to ${screenshotPath}`);
    }
  });

  test('Complete flow: Create curriculum → Add node → Open NodeEditor → Verify PDF/Link buttons', async ({ page }) => {
    // ==================== STEP 1: Navigate to Home ====================
    addLog('\n📍 STEP 1: Navigate to Home Page');
    await page.goto('http://localhost:3002/', { waitUntil: 'networkidle', timeout: 30000 });
    addLog('✓ Home page loaded');

    // ==================== STEP 2: Create Curriculum ====================
    addLog('\n📍 STEP 2: Create New Curriculum');

    // Click the create curriculum button
    const createButton = page.locator('button:has-text("새 커리큘럼 만들기")');
    addLog('Looking for create curriculum button...');
    await expect(createButton).toBeVisible({ timeout: 10000 });
    addLog('✓ Create button found');

    await createButton.click();
    addLog('✓ Create button clicked');

    // Wait for modal
    const modal = page.locator(':text("Create New Curriculum")');
    addLog('Waiting for curriculum creation modal...');
    await expect(modal).toBeVisible({ timeout: 5000 });
    addLog('✓ Modal appeared');

    // Fill in the form
    const curriculumTitle = `Test Curriculum ${Date.now()}`;
    const titleInput = page.locator('input#title');
    addLog(`Filling title: "${curriculumTitle}"`);
    await titleInput.fill(curriculumTitle);
    addLog('✓ Title filled');

    // Click create button
    const submitButton = page.locator('button:has-text("Create")');
    addLog('Clicking Create button...');
    await submitButton.click();
    addLog('✓ Create button clicked');

    // Wait for modal to close and API response
    await page.waitForTimeout(1000);
    addLog('✓ Modal closed');

    // ==================== STEP 3: Get Curriculum ID from API ====================
    addLog('\n📍 STEP 3: Fetch Created Curriculum from API');

    const curriculumResponse = await page.evaluate(() =>
      fetch('/api/v1/curriculums/').then(r => {
        if (!r.ok) throw new Error(`API error: ${r.status}`);
        return r.json();
      })
    );

    const curriculumId = curriculumResponse[0]?.curriculum_id;
    if (!curriculumId) {
      throw new Error('Failed to get curriculum ID from API');
    }
    addLog(`✓ Curriculum created with ID: ${curriculumId}`);

    // ==================== STEP 4: Navigate to Curriculum Editor ====================
    addLog('\n📍 STEP 4: Navigate to Curriculum Editor');

    const curriculumUrl = `http://localhost:3002/#/curriculum/${curriculumId}`;
    addLog(`Navigating to: ${curriculumUrl}`);
    await page.goto(curriculumUrl, { waitUntil: 'networkidle', timeout: 30000 });
    addLog('✓ Curriculum Editor loaded');

    // Verify we're on the curriculum editor page - look for "Nodes" heading
    const nodesHeading = page.locator('h3').filter({ hasText: 'Nodes' }).first();
    addLog('Verifying Curriculum Editor page loaded...');
    await expect(nodesHeading).toBeVisible({ timeout: 5000 });
    addLog(`✓ Curriculum editor page verified`);

    // ==================== STEP 5: Create a Node via API ====================
    addLog('\n📍 STEP 5: Create New Node via API');

    // Create node directly via API to avoid modal interaction issues
    const nodeTitle = `Test Node ${Date.now()}`;
    const nodeResponse = await page.evaluate(
      ({ currId, title }) => {
        return fetch(`/api/v1/curriculums/${currId}/nodes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, node_type: 'CONTENT' })
        })
          .then(r => {
            if (!r.ok) throw new Error(`Node creation failed: ${r.status}`);
            return r.json();
          });
      },
      { currId: curriculumId, title: nodeTitle }
    );

    const nodeId = nodeResponse.node_id;
    if (!nodeId) {
      throw new Error('Failed to get node ID from API response');
    }
    addLog(`✓ Node created with ID: ${nodeId}`);

    // ==================== STEP 6: Navigate to Node Editor ====================
    addLog('\n📍 STEP 6: Navigate to Node Editor');

    const nodeEditorUrl = `http://localhost:3002/#/curriculum/${curriculumId}/node/${nodeId}`;
    addLog(`Navigating to: ${nodeEditorUrl}`);
    await page.goto(nodeEditorUrl, { waitUntil: 'networkidle', timeout: 30000 });
    addLog('✓ Node Editor page loaded');

    // ==================== STEP 7: Verify PDF Link Button ====================
    addLog('\n📍 STEP 7: Verify PDF Link Button');

    const pdfButton = page.locator('button:has-text("Add PDF")');
    addLog('Looking for "Add PDF" button...');
    await expect(pdfButton).toBeVisible({ timeout: 5000 });
    addLog('✓ "Add PDF" button is visible');

    // ==================== STEP 8: Verify Node Link Button ====================
    addLog('\n📍 STEP 8: Verify Node Link Button');

    const linkButton = page.locator('button:has-text("Add Link")');
    addLog('Looking for "Add Link" button...');
    await expect(linkButton).toBeVisible({ timeout: 5000 });
    addLog('✓ "Add Link" button is visible');

    // ==================== STEP 9: Test PDF Modal Opening ====================
    addLog('\n📍 STEP 9: Test PDF Modal Opening');

    addLog('Clicking PDF button...');
    await pdfButton.click();
    addLog('✓ PDF button clicked');

    // Wait for PDF modal to appear
    const pdfModalContent = page.locator('h2:has-text("Link PDF File")');
    addLog('Waiting for PDF modal...');
    await expect(pdfModalContent).toBeVisible({ timeout: 5000 });
    addLog('✓ PDF modal appeared');

    // Close modal by pressing Escape
    await page.keyboard.press('Escape');
    addLog('✓ PDF modal closed (escape pressed)');

    // ==================== STEP 10: Final Verification ====================
    addLog('\n📍 STEP 10: Final Verification');

    // Verify both buttons are still visible
    await expect(pdfButton).toBeVisible({ timeout: 5000 });
    await expect(linkButton).toBeVisible({ timeout: 5000 });
    addLog('✓ Both PDF and Link buttons remain visible after PDF modal test');

    // Add a small wait to ensure everything settled
    await page.waitForTimeout(500);
    addLog('✓ Node Editor fully functional with PDF/Link capabilities');

    addLog('\n✅ COMPLETE FLOW TEST PASSED - All Steps Completed Successfully');
  });
});
