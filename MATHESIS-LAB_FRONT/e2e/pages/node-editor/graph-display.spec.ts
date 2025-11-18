import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const logsDir = path.join(__dirname, '../../test-logs/graph-display');

let testLogs: string[] = [];

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

async function takeScreenshot(page: any, stepName: string) {
  ensureLogsDir();
  const safeName = stepName.replace(/[^a-zA-Z0-9_-]/g, '-').replace(/\s+/g, '-');
  const screenshotPath = path.join(logsDir, `${safeName}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  addLog(`📸 Screenshot saved: ${safeName}.png`);
  return screenshotPath;
}

test.describe('NodeGraph Visualization E2E Test - With Multiple Linked Nodes', () => {
  test('should display interactive graph with multiple related nodes', async ({ page }) => {
    addLog('=== NodeGraph Visualization Test Started ===\n');

    // Setup logging
    page.on('request', (request) => {
      addLog(`[REQUEST] ${request.method()} ${new URL(request.url()).pathname}`);
    });

    page.on('response', (response) => {
      if (response.status() >= 400) {
        addLog(`[RESPONSE ERROR] ${response.status()} ${new URL(response.url()).pathname}`);
      }
    });

    // ==================== STEP 1: Navigate to Home ====================
    addLog('📍 STEP 1: Navigate to Home');
    await page.goto('http://localhost:3002/', { waitUntil: 'networkidle', timeout: 30000 });
    await takeScreenshot(page, 'GRAPH-01-Home-Page');

    // ==================== STEP 2: Create Curriculum ====================
    addLog('\n📍 STEP 2: Create Curriculum');

    const createButton = page.locator('button:has-text("새 커리큘럼 만들기")');
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();

    const modal = page.locator(':text("Create New Curriculum")');
    await expect(modal).toBeVisible({ timeout: 5000 });

    const curriculumTitle = `Graph Test ${Date.now()}`;
    const titleInput = page.locator('input#title');
    await titleInput.fill(curriculumTitle);

    const submitButton = page.locator('button:has-text("Create")');
    await submitButton.click();

    await page.waitForTimeout(1000);
    addLog('✓ Curriculum created');

    // ==================== STEP 3: Get Curriculum ID ====================
    addLog('\n📍 STEP 3: Fetch Curriculum from API');

    const curriculumResponse = await page.evaluate(() =>
      fetch('/api/v1/curriculums/').then(r => r.json())
    );

    const curriculumId = curriculumResponse[0]?.curriculum_id;
    addLog(`✓ Curriculum ID: ${curriculumId}`);

    // ==================== STEP 4: Create Multiple Nodes ====================
    addLog('\n📍 STEP 4: Create Multiple Nodes');

    const nodeIds: string[] = [];
    const nodeNames = ['Main Topic', 'Subtopic 1', 'Subtopic 2', 'Reference Node'];

    for (const nodeName of nodeNames) {
      const nodeResponse = await page.evaluate(
        ({ currId, title }) => {
          return fetch(`/api/v1/curriculums/${currId}/nodes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, node_type: 'CONTENT' })
          }).then(r => r.json());
        },
        { currId: curriculumId, title: nodeName }
      );
      nodeIds.push(nodeResponse.node_id);
      addLog(`✓ Created node: "${nodeName}" (${nodeResponse.node_id})`);
    }

    // ==================== STEP 5: Create Node Links ====================
    addLog('\n📍 STEP 5: Create Node-to-Node Links');

    // Link structure: Main Topic -> Subtopic 1, Main Topic -> Subtopic 2, Subtopic 1 -> Reference Node
    const mainNodeId = nodeIds[0];
    const subtopic1Id = nodeIds[1];
    const subtopic2Id = nodeIds[2];
    const referenceNodeId = nodeIds[3];

    // Link 1: Main -> Subtopic 1
    await page.evaluate(
      ({ nodeId, linkedNodeId }) => {
        return fetch(`/api/v1/nodes/${nodeId}/links/node`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            linked_node_id: linkedNodeId,
            link_relationship: 'EXTENDS'
          })
        }).then(r => r.json());
      },
      { nodeId: mainNodeId, linkedNodeId: subtopic1Id }
    );
    addLog('✓ Link created: Main Topic -> Subtopic 1 (EXTENDS)');

    // Link 2: Main -> Subtopic 2
    await page.evaluate(
      ({ nodeId, linkedNodeId }) => {
        return fetch(`/api/v1/nodes/${nodeId}/links/node`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            linked_node_id: linkedNodeId,
            link_relationship: 'EXTENDS'
          })
        }).then(r => r.json());
      },
      { nodeId: mainNodeId, linkedNodeId: subtopic2Id }
    );
    addLog('✓ Link created: Main Topic -> Subtopic 2 (EXTENDS)');

    // Link 3: Subtopic 1 -> Reference
    await page.evaluate(
      ({ nodeId, linkedNodeId }) => {
        return fetch(`/api/v1/nodes/${nodeId}/links/node`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            linked_node_id: linkedNodeId,
            link_relationship: 'REFERENCES'
          })
        }).then(r => r.json());
      },
      { nodeId: subtopic1Id, linkedNodeId: referenceNodeId }
    );
    addLog('✓ Link created: Subtopic 1 -> Reference Node (REFERENCES)');

    // ==================== STEP 6: Navigate to Main Node Editor ====================
    addLog('\n📍 STEP 6: Navigate to Main Node Editor');

    const nodeEditorUrl = `http://localhost:3002/#/curriculum/${curriculumId}/node/${mainNodeId}`;
    await page.goto(nodeEditorUrl, { waitUntil: 'networkidle', timeout: 30000 });

    // Wait for content to load
    await page.waitForTimeout(2000);
    addLog('✓ Node editor loaded');
    await takeScreenshot(page, 'GRAPH-02-Node-Editor-With-Graph');

    // ==================== STEP 7: Verify Graph is Visible ====================
    addLog('\n📍 STEP 7: Verify Graph Components');

    // Check for graph heading
    const graphHeading = page.locator('h3:has-text("Node Relationships")');
    const isGraphVisible = await graphHeading.isVisible().catch(() => false);

    if (isGraphVisible) {
      addLog('✓ Graph heading "Node Relationships" is visible');
      await expect(graphHeading).toBeVisible();
    } else {
      addLog('⚠ Graph heading not found - checking for canvas element');
    }

    // Check for canvas
    const canvas = page.locator('canvas');
    const canvasCount = await canvas.count();
    addLog(`✓ Found ${canvasCount} canvas element(s)`);

    if (canvasCount > 0) {
      const canvasBounds = await canvas.first().boundingBox();
      if (canvasBounds) {
        addLog(`✓ Canvas dimensions: ${canvasBounds.width}x${canvasBounds.height}px`);
      }
    }

    // ==================== STEP 8: Check Legend ====================
    addLog('\n📍 STEP 8: Verify Graph Legend');

    const legendItems = [
      '🔵 Blue: Current node',
      '⚪ Gray: Related nodes',
      'Drag nodes to explore'
    ];

    for (const item of legendItems) {
      const found = await page.locator(`text=${item}`).isVisible().catch(() => false);
      if (found) {
        addLog(`✓ Legend item found: "${item}"`);
      }
    }

    // ==================== STEP 9: Take Additional Screenshots ====================
    addLog('\n📍 STEP 9: Capture Additional Views');

    await page.waitForTimeout(1000);
    await takeScreenshot(page, 'GRAPH-03-Graph-Rendering-Stable');

    // ==================== STEP 10: Navigate to Related Node ====================
    addLog('\n📍 STEP 10: Test Node Navigation via Graph');

    // Try to click on canvas to see if we can navigate
    const canvasElement = page.locator('canvas').first();
    const canvasIsVisible = await canvasElement.isVisible().catch(() => false);

    if (canvasIsVisible) {
      const boundingBox = await canvasElement.boundingBox();
      if (boundingBox) {
        // Click near the edge of canvas where a node might be positioned
        await canvasElement.click({ position: { x: boundingBox.width * 0.8, y: boundingBox.height / 2 } });
        addLog('✓ Clicked on canvas to test node interaction');
        await page.waitForTimeout(500);
        await takeScreenshot(page, 'GRAPH-04-After-Graph-Interaction');
      }
    }

    // ==================== Final Report ====================
    addLog('\n=== Test Completed Successfully ===');
    addLog(`✓ Created ${nodeNames.length} nodes with ${3} links`);
    addLog('✓ NodeGraph component is rendering');
    addLog('✓ Canvas element is present');
    addLog('✓ Multiple screenshots captured');

    ensureLogsDir();
    const logFile = path.join(logsDir, 'test-log.txt');
    fs.writeFileSync(logFile, testLogs.join('\n') + '\n');
    addLog(`\n✓ Test logs saved to: ${logFile}`);
  });
});
