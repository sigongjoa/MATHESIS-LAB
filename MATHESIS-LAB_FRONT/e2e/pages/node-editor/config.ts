/**
 * Node Editor Page Test Configuration
 *
 * PDF 업로드 및 노드-투-노드 링크 관리 테스트 설정
 */

export const NODE_EDITOR_CONFIG = {
  name: 'Node Editor Page',
  baseUrl: 'http://localhost:3002/#/curriculum',

  // 페이지 요소 선택자
  selectors: {
    // 헤더
    heading: 'h1:has-text("Node Editor")',

    // PDF 링크 모달
    createPDFLinkButton: 'button:has-text("Add PDF")',
    pdfLinkModal: '[role="dialog"]:has-text("PDF")',
    pdfFileInput: 'input[type="file"]',
    pdfUrlInput: 'input[placeholder*="URL"]',
    pdfSubmitButton: 'button:has-text("Add")',

    // 노드-투-노드 링크 모달
    createNodeLinkButton: 'button:has-text("Link Node")',
    nodeSelectDropdown: 'select[name*="node"]',
    nodeRelationshipSelect: 'select[name*="relationship"]',
    nodeSubmitButton: 'button:has-text("Create Link")',

    // 링크 관리 섹션
    linkManager: '[class*="link"], [class*="manager"]',
    linkItem: '[class*="link-item"], [class*="resource"]',
    deleteLinkButton: 'button:has-text("Delete")',

    // 노드 콘텐츠
    contentInput: 'textarea[placeholder*="content"]',
    markdownContent: '[class*="markdown"], [class*="content"]',
  },

  // 테스트 체크리스트
  checks: [
    {
      selector: 'button:has-text("Add PDF")',
      expectVisible: true,
      description: 'PDF 링크 생성 버튼 표시 확인',
    },
    {
      selector: 'button:has-text("Link Node")',
      expectVisible: true,
      description: '노드-투-노드 링크 생성 버튼 표시 확인',
    },
  ],

  // 테스트 시간 초과 설정
  timeouts: {
    navigation: 15000,
    waitForElement: 5000,
    uploadFile: 10000,
  },

  // 예상 네트워크 요청 수
  expectedRequests: {
    min: 40,
    max: 100,
  },

  // 예상 콘솔 에러 수
  expectedErrors: 0,
};
