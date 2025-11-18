import { test, expect } from '@playwright/test';

test('Debug: Check if NodeGraph is in DOM', async ({ page }) => {
  // Create basic setup (same as graph-display.spec.ts but simpler)
  await page.goto('http://localhost:3002/', { waitUntil: 'networkidle', timeout: 30000 });

  // Create curriculum
  const createButton = page.locator('button:has-text("새 커리큘럼 만들기")');
  await expect(createButton).toBeVisible({ timeout: 10000 });
  await createButton.click();

  const modal = page.locator(':text("Create New Curriculum")');
  await expect(modal).toBeVisible({ timeout: 5000 });

  const titleInput = page.locator('input#title');
  await titleInput.fill(`Debug Test ${Date.now()}`);

  const submitButton = page.locator('button:has-text("Create")');
  await submitButton.click();

  await page.waitForTimeout(1000);

  // Get curriculum
  const curriculumResponse = await page.evaluate(() =>
    fetch('/api/v1/curriculums/').then(r => r.json())
  );

  const curriculumId = curriculumResponse[0]?.curriculum_id;

  // Create node
  const nodeResponse = await page.evaluate(
    ({ currId, title }) => {
      return fetch(`/api/v1/curriculums/${currId}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, node_type: 'CONTENT' })
      }).then(r => r.json());
    },
    { currId: curriculumId, title: 'Test Node' }
  );

  const nodeId = nodeResponse.node_id;

  // Create another node for linking
  const nodeResponse2 = await page.evaluate(
    ({ currId, title }) => {
      return fetch(`/api/v1/curriculums/${currId}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, node_type: 'CONTENT' })
      }).then(r => r.json());
    },
    { currId: curriculumId, title: 'Linked Node' }
  );

  const nodeId2 = nodeResponse2.node_id;

  // Create link
  await page.evaluate(
    ({ nodeId: nId, linkedNodeId }) => {
      return fetch(`/api/v1/nodes/${nId}/links/node`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          linked_node_id: linkedNodeId,
          link_relationship: 'EXTENDS'
        })
      }).then(r => r.json());
    },
    { nodeId: nodeId, linkedNodeId: nodeId2 }
  );

  // Navigate to node editor
  const nodeEditorUrl = `http://localhost:3002/#/curriculum/${curriculumId}/node/${nodeId}`;
  await page.goto(nodeEditorUrl, { waitUntil: 'networkidle', timeout: 30000 });

  // Wait for data to load
  await page.waitForTimeout(3000);

  // Wait for specific elements to indicate loading is done
  const nodeTitle = page.locator('h1:has-text("Test Node")');
  await nodeTitle.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});

  await page.waitForTimeout(2000);

  // ===== DEBUG CHECKS =====
  console.log('\n=== DOM Analysis ===');

  // Check if NodeEditor component rendered
  const nodeEditorMain = page.locator('main');
  const mainExists = await nodeEditorMain.count();
  console.log(`✓ Main element exists: ${mainExists > 0}`);

  // Check for LinkManager
  const linkManager = page.locator('text=PDF Files');
  const linkManagerExists = await linkManager.isVisible().catch(() => false);
  console.log(`✓ LinkManager visible: ${linkManagerExists}`);

  // Check for NodeGraph heading
  const graphHeading = page.locator('h3:has-text("Node Relationships")');
  const graphHeadingExists = await graphHeading.isVisible().catch(() => false);
  console.log(`✓ Graph heading visible: ${graphHeadingExists}`);

  // Check for canvas
  const canvas = page.locator('canvas');
  const canvasCount = await canvas.count();
  console.log(`✓ Canvas elements found: ${canvasCount}`);

  // Get full HTML to debug
  const fullHtml = await page.content();

  // Check if NodeGraph import is in the page source
  const hasNodeGraphImport = fullHtml.includes('NodeGraph');
  console.log(`✓ "NodeGraph" found in HTML: ${hasNodeGraphImport}`);

  // Print grid structure
  console.log('\n=== Grid Structure Debug ===');
  if (fullHtml.includes('lg:grid-cols-4')) {
    console.log('✓ Has lg:grid-cols-4');
  }
  const gridMatches = fullHtml.match(/lg:col-span-\d/g) || [];
  console.log(`✓ Found ${gridMatches.length} grid col span elements`);

  // Check the main element
  const mainMatch = fullHtml.match(/<main[^>]*>[\s\S]{0,1000}/);
  if (mainMatch) {
    console.log('Main tag attributes:', mainMatch[0].substring(0, 100));
  }

  const hasNodeRelationships = fullHtml.includes('Node Relationships');
  console.log(`✓ "Node Relationships" text in HTML: ${hasNodeRelationships}`);

  // Check sidebar structure
  const sidebarDiv = page.locator('div.lg\\:col-span-2');
  const sidebarCount = await sidebarDiv.count();
  console.log(`✓ Sidebar divs (lg:col-span-2): ${sidebarCount}`);

  // Get total height of page
  const pageHeight = await page.evaluate(() => {
    return document.documentElement.scrollHeight;
  });
  console.log(`✓ Page height: ${pageHeight}px`);

  // Get viewport height
  const viewportSize = page.viewportSize();
  console.log(`✓ Viewport height: ${viewportSize?.height}px`);

  // Scroll down to see if graph appears
  console.log('\n=== Scrolling Test ===');
  await page.evaluate(() => {
    window.scrollBy(0, 500);
  });

  await page.waitForTimeout(500);

  const graphHeadingAfterScroll = page.locator('h3:has-text("Node Relationships")');
  const graphHeadingAfterScrollExists = await graphHeadingAfterScroll.isVisible().catch(() => false);
  console.log(`✓ Graph heading visible after scroll: ${graphHeadingAfterScrollExists}`);

  const canvasAfterScroll = page.locator('canvas');
  const canvasCountAfterScroll = await canvasAfterScroll.count();
  console.log(`✓ Canvas elements after scroll: ${canvasCountAfterScroll}`);

  // Scroll to bottom
  await page.evaluate(() => {
    window.scrollTo(0, document.documentElement.scrollHeight);
  });

  await page.waitForTimeout(500);

  const graphHeadingAtBottom = page.locator('h3:has-text("Node Relationships")');
  const graphHeadingAtBottomExists = await graphHeadingAtBottom.isVisible().catch(() => false);
  console.log(`✓ Graph heading visible at bottom: ${graphHeadingAtBottomExists}`);

  // Take final screenshot
  await page.screenshot({ path: '/tmp/debug-graph-final.png', fullPage: true });
  console.log('\n✓ Full page screenshot saved to /tmp/debug-graph-final.png');
});
