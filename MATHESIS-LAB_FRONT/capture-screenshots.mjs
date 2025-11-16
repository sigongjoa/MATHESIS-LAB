import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  await page.setViewportSize({ width: 1280, height: 720 });
  
  try {
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    await page.screenshot({ 
      path: '/mnt/d/progress/MATHESIS LAB/docs/frontend-main.png'
    });
    console.log('✅ Screenshot saved: frontend-main.png');
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
})();
