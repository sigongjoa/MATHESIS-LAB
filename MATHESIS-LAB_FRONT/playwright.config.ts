import { defineConfig, devices } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

/**
 * 테스트 설정 파일 읽기
 * 중앙화된 설정으로 포트 등을 동적으로 설정
 */
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const configPath = path.resolve(__dirname, '../test.config.json');
let testConfig: any = {
  frontend: { port: 3002, host: '0.0.0.0' },
  backend: { port: 8000, host: '0.0.0.0' }
};

if (fs.existsSync(configPath)) {
  testConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
}

const FRONTEND_PORT = process.env.FRONTEND_PORT || testConfig.frontend.port;
const FRONTEND_HOST = process.env.FRONTEND_HOST || testConfig.frontend.host;

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './e2e',

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,

  /* Reporter to use */
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list']
  ],

  /* Global timeout */
  timeout: 30 * 1000,

  /* Expect timeout */
  expect: { timeout: 5 * 1000 },

  /* Shared settings for all the projects */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: `http://localhost:${FRONTEND_PORT}`,

    /* Collect trace when retrying the failed test. */
    trace: 'on-first-retry',

    /* Take screenshot on every test */
    screenshot: 'only-on-failure',

    /* Video on every test */
    video: 'retain-on-failure',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
      },
    },

    // 로컬 테스트에서는 Chromium만 사용
    // CI/CD에서는 필요시 다른 브라우저 추가
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: `npm run dev -- --host ${FRONTEND_HOST} --port ${FRONTEND_PORT}`,
    url: `http://localhost:${FRONTEND_PORT}`,
    reuseExistingServer: true,  // Reuse existing server if already running
    timeout: 120 * 1000,
  },
});
