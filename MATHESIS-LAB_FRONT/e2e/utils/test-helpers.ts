/**
 * E2E Test Helper Functions
 *
 * 테스트에서 자주 사용하는 유틸리티 함수들
 */

import { Page, expect } from '@playwright/test';
import { shouldIgnoreConsoleError } from '../shared/test-config';

/**
 * 페이지 네비게이션 헬퍼
 */
export async function navigateToPage(page: Page, url: string, timeout: number = 15000) {
  await page.goto(url, {
    waitUntil: 'networkidle',
    timeout,
  });
}

/**
 * 콘솔 에러 캡처 및 필터링
 */
export async function captureConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const errorText = msg.text();
      if (!shouldIgnoreConsoleError(errorText)) {
        errors.push(errorText);
      }
    }
  });

  // 페이지 로드 완료 대기
  await page.waitForLoadState('networkidle');

  return errors;
}

/**
 * 요소 가시성 확인
 */
export async function assertElementVisible(page: Page, selector: string, description?: string) {
  const element = page.locator(selector);
  await expect(element).toBeVisible();
  if (description) {
    console.log(`✅ ${description}`);
  }
}

/**
 * 요소 텍스트 확인
 */
export async function assertElementText(
  page: Page,
  selector: string,
  expectedText: string,
  description?: string
) {
  const element = page.locator(selector);
  await expect(element).toContainText(expectedText);
  if (description) {
    console.log(`✅ ${description}`);
  }
}

/**
 * 네트워크 요청 통계
 */
export interface NetworkStats {
  totalRequests: number;
  successRequests: number;
  failedRequests: number;
  requestsByType: Record<string, number>;
}

export async function captureNetworkStats(page: Page): Promise<NetworkStats> {
  const requests: { url: string; status: number; type: string }[] = [];

  page.on('response', (response) => {
    const url = response.url();
    const type = url.split('.').pop()?.split('?')[0] || 'unknown';

    requests.push({
      url,
      status: response.status(),
      type,
    });
  });

  // 페이지 로드 완료 대기
  await page.waitForLoadState('networkidle');

  const stats: NetworkStats = {
    totalRequests: requests.length,
    successRequests: requests.filter((r) => r.status >= 200 && r.status < 300).length,
    failedRequests: requests.filter((r) => r.status >= 400).length,
    requestsByType: {},
  };

  requests.forEach((r) => {
    stats.requestsByType[r.type] = (stats.requestsByType[r.type] || 0) + 1;
  });

  return stats;
}

/**
 * 테스트 체크 인터페이스
 */
export interface TestCheck {
  selector: string;
  expectText?: string | null;
  expectVisible?: boolean | null;
  description?: string;
}

/**
 * 여러 체크 항목 실행
 */
export async function runChecks(page: Page, checks: TestCheck[]): Promise<boolean> {
  let allPassed = true;

  for (const check of checks) {
    try {
      if ('expectText' in check && check.expectText !== null) {
        const element = page.locator(check.selector);
        const text = await element.textContent();
        const passed = text && text.includes(check.expectText);

        if (passed) {
          console.log(`✅ ${check.description || `Text "${check.expectText}" found in ${check.selector}`}`);
        } else {
          console.log(`❌ ${check.description || `Text "${check.expectText}" not found in ${check.selector}`}`);
          allPassed = false;
        }
      } else if ('expectVisible' in check && check.expectVisible !== null) {
        const element = page.locator(check.selector);
        const visible = await element.isVisible();

        if (visible) {
          console.log(`✅ ${check.description || `Element ${check.selector} is visible`}`);
        } else {
          console.log(`❌ ${check.description || `Element ${check.selector} is not visible`}`);
          allPassed = false;
        }
      }
    } catch (error) {
      console.log(`⚠️ Error checking ${check.selector}: ${error}`);
      allPassed = false;
    }
  }

  return allPassed;
}

/**
 * 스크린샷 캡처
 */
export async function takeScreenshot(
  page: Page,
  filename: string,
  outputDir: string = './test-report-with-logs/screenshots'
) {
  await page.screenshot({
    path: `${outputDir}/${filename}.png`,
    fullPage: false,
  });
}

/**
 * 텍스트 로깅
 */
export function logTestStart(testName: string) {
  console.log(`\n🧪 Testing: ${testName}`);
}

export function logSuccess(message: string) {
  console.log(`✅ ${message}`);
}

export function logError(message: string) {
  console.log(`❌ ${message}`);
}

export function logWarning(message: string) {
  console.log(`⚠️ ${message}`);
}
