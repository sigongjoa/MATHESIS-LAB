/**
 * GCP Settings Page Test Configuration
 *
 * 페이지별 테스트 설정을 중앙화하여 관리
 * - URL: 테스트할 페이지 경로
 * - selectors: 페이지 요소 선택자 (변경 시 한 곳에서만 수정)
 * - checks: 테스트 시 확인할 항목들
 */

export const GCP_SETTINGS_CONFIG = {
  name: 'GCP Settings Page',
  url: 'http://localhost:3002/#/gcp-settings',

  // 페이지 요소 선택자
  selectors: {
    // 헤더
    heading: 'h1:has-text("GCP Settings")',
    subtitle: 'p:has-text("Manage Google Cloud Platform")',

    // 탭
    tabs: {
      overview: 'button:has-text("Overview")',
      backup: 'button:has-text("Backup & Restore")',
      sync: 'button:has-text("Multi-Device Sync")',
    },

    // 상태 카드
    statusCard: '.status-card',
    statusHeading: 'h3:has-text("GCP Integration Status")',

    // 기능 섹션
    featuresHeading: 'h3:has-text("Available Features")',
    featureCards: '.feature-card',

    // 버튼
    buttons: {
      refresh: 'button:has-text("Refresh Status")',
      healthCheck: 'button:has-text("Health Check")',
    },
  },

  // 테스트 체크리스트
  checks: [
    {
      selector: 'h1',
      expectText: 'GCP Settings',
      description: 'GCP Settings 제목 표시 확인',
    },
    {
      selector: 'h3:has-text("Available Features")',
      expectVisible: true,
      description: 'Available Features 섹션 표시 확인',
    },
    {
      selector: 'h3:has-text("GCP Integration Status")',
      expectVisible: true,
      description: 'GCP Integration Status 섹션 표시 확인',
    },
    {
      selector: 'button:has-text("Refresh Status")',
      expectVisible: true,
      description: 'Refresh Status 버튼 표시 확인',
    },
    {
      selector: 'button:has-text("Health Check")',
      expectVisible: true,
      description: 'Health Check 버튼 표시 확인',
    },
  ],

  // 테스트 시간 초과 설정
  timeouts: {
    navigation: 15000,
    waitForElement: 5000,
  },

  // 예상 네트워크 요청 수
  expectedRequests: {
    min: 30,
    max: 60,
  },

  // 예상 콘솔 에러 수
  expectedErrors: 0,
};
