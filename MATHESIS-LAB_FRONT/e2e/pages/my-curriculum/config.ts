/**
 * My Curriculum Page Test Configuration
 *
 * 사용자의 커리큘럼 목록 페이지 테스트 설정
 */

export const MY_CURRICULUM_CONFIG = {
  name: 'My Curriculum Page',
  url: 'http://localhost:3002/',

  // 페이지 요소 선택자
  selectors: {
    // 헤더
    heading: 'h1:has-text("내 커리큘럼")',
    createButton: 'button:has-text("새 커리큘럼 만들기")',

    // 커리큘럼 항목
    curriculumItem: '[class*="curriculum"], [class*="card"]',
    curriculumLink: 'a[href*="/curriculum/"]',

    // 모달
    createModal: '[role="dialog"]',
    modalInput: 'input[placeholder*="커리큘럼"]',
    modalSubmit: 'button:has-text("생성")',
  },

  // 테스트 체크리스트
  checks: [
    {
      selector: 'h1',
      expectVisible: true,
      description: '페이지 제목 표시 확인',
    },
    {
      selector: 'button',
      expectVisible: true,
      description: '버튼 요소 표시 확인',
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
    max: 80,
  },

  // 예상 콘솔 에러 수
  expectedErrors: 0,
};
