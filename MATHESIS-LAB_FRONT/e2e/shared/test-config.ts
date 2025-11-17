/**
 * Shared E2E Test Configuration
 *
 * 모든 E2E 테스트에서 사용하는 공통 설정
 */

export const COMMON_TIMEOUTS = {
  SHORT: 3000,
  MEDIUM: 5000,
  LONG: 10000,
  NAVIGATION: 15000,
  PAGE_LOAD: 30000,
};

export const COMMON_SELECTORS = {
  // 헤더
  LOGO: 'text=MATHESIS LAB',
  HEADER: 'header',

  // 네비게이션
  NAV_BROWSE: 'a:has-text("Browse")',
  NAV_MY_CURRICULUM: 'a:has-text("My Curriculum")',
  NAV_GCP_SETTINGS: 'a:has-text("GCP Settings")',

  // 버튼
  BUTTON: 'button',
  SIGN_IN: 'button:has-text("로그인")',
  CREATE: 'button:has-text("생성")',
  SUBMIT: 'button:has-text("제출")',
  CANCEL: 'button:has-text("취소")',

  // 입력
  INPUT: 'input',
  TEXTAREA: 'textarea',

  // 모달
  MODAL: '[role="dialog"]',
  MODAL_CLOSE: '[role="dialog"] button:has-text("✕")',

  // 에러 메시지
  ERROR: '[class*="error"]',
  SUCCESS: '[class*="success"]',
};

export const TEST_CONFIG = {
  // 기본 타임아웃 설정
  timeout: COMMON_TIMEOUTS.MEDIUM,

  // 네트워크 아이들 상태 대기 설정
  networkIdle: true,

  // 콘솔 에러 필터
  ignoreConsoleErrors: [
    'cdn.tailwindcss.com',
    'GSI_LOGGER',
    'Origin is not allowed',
    'Provided button width',
    'React DevTools',
  ],

  // 네트워크 에러 필터
  ignoreNetworkErrors: [
    403, // Forbidden (Google Sign-In 등)
    401, // Unauthorized
  ],

  // 테스트 보고서 생성 설정
  reportConfig: {
    outputDir: './test-report-with-logs',
    screenshotsDir: './test-report-with-logs/screenshots',
    logsDir: './test-report-with-logs/logs',
  },
};

/**
 * 콘솔 에러가 무시해야 할 패턴인지 확인
 */
export function shouldIgnoreConsoleError(error: string): boolean {
  return TEST_CONFIG.ignoreConsoleErrors.some((pattern) => error.includes(pattern));
}

/**
 * 네트워크 에러가 무시해야 할 상태 코드인지 확인
 */
export function shouldIgnoreNetworkError(status: number): boolean {
  return TEST_CONFIG.ignoreNetworkErrors.includes(status);
}
