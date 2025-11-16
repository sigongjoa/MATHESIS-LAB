const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Set viewport to capture full UI
  await page.setViewportSize({ width: 1280, height: 720 });
  
  try {
    // Navigate to the app
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    
    // Take screenshot of main page
    await page.screenshot({ 
      path: '/mnt/d/progress/MATHESIS LAB/docs/frontend-main.png',
      fullPage: false
    });
    
    console.log('✅ Screenshot captured: frontend-main.png');
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
})();
