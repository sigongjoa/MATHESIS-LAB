/**
 * Browse Curriculums Page Test Configuration
 *
 * 모든 커리큘럼 둘러보기 페이지 테스트 설정
 */

export const BROWSE_CURRICULUMS_CONFIG = {
  name: 'Browse Curriculums Page',
  url: 'http://localhost:3002/#/browse',

  // 페이지 요소 선택자
  selectors: {
    // 헤더
    heading: 'p:has-text("모든 커리큘럼 둘러보기")',
    logo: 'text=MATHESIS LAB',

    // 네비게이션
    browseLink: 'a:has-text("Browse All")',
    myCurriculumLink: 'a:has-text("My Curriculum")',

    // 검색
    searchInput: 'input[placeholder*="커리큘럼"]',

    // 커리큘럼 카드
    curriculumCards: '.group[class*="container"]',
    cardLink: 'a[href*="/curriculum/"]',

    // 로그인
    signInButton: 'button:has-text("로그인")',
  },

  // 테스트 체크리스트
  checks: [
    {
      selector: 'button',
      expectVisible: true,
      description: '버튼 요소 표시 확인',
    },
    {
      selector: 'p:has-text("모든 커리큘럼")',
      expectVisible: true,
      description: '페이지 제목 표시 확인',
    },
  ],

  // 테스트 시간 초과 설정
  timeouts: {
    navigation: 15000,
    waitForElement: 5000,
  },

  // 예상 네트워크 요청 수
  expectedRequests: {
    min: 40,
    max: 80,
  },

  // 예상 콘솔 에러 수 (GSI 인증 에러 제외)
  expectedErrors: {
    // GSI 에러는 개발 환경에서 발생 가능
    ignorePatterns: ['GSI_LOGGER', 'Origin is not allowed', 'Provided button width'],
  },
};
