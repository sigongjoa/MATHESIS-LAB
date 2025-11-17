/**
 * Home (My Curriculum) Page Test Configuration
 *
 * 내 커리큘럼 페이지 테스트 설정
 */

export const HOME_CONFIG = {
  name: 'Home Page',
  url: 'http://localhost:3002/',

  // 페이지 요소 선택자
  selectors: {
    // 헤더
    logo: 'text=MATHESIS LAB',
    heading: 'h1:has-text("내 커리큘럼 관리")',

    // 네비게이션
    browseLink: 'a:has-text("Browse All")',
    myCurriculumLink: 'a:has-text("My Curriculum")',

    // 버튼
    createButton: 'button:has-text("새 커리큘럼 만들기")',
    signInButton: 'button:has-text("로그인")',

    // 콘텐츠
    curriculumList: '.grid, [class*="list"], [class*="container"]',
  },

  // 테스트 체크리스트
  checks: [
    {
      selector: 'h1',
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
    min: 30,
    max: 80,
  },

  // 예상 콘솔 에러 수
  expectedErrors: 0,
};
