# MATHESIS LAB 프론트엔드 테스트 구조 정리

## 📋 개요

프론트엔드 E2E 테스트를 **페이지별 폴더 구조**로 정리하여 관리와 확장이 용이하도록 변경했습니다.

## 📁 새로운 폴더 구조

```
MATHESIS-LAB_FRONT/
├── e2e/                                    # 모든 E2E 테스트
│   ├── pages/                              # ✨ 페이지별 테스트 (새로운 구조)
│   │   ├── gcp-settings/
│   │   │   ├── config.ts                   # 페이지 설정 (URL, 선택자, 타임아웃)
│   │   │   └── gcp-settings.spec.ts        # 테스트 스펙
│   │   ├── browse-curriculums/
│   │   │   ├── config.ts
│   │   │   └── browse-curriculums.spec.ts
│   │   ├── home/
│   │   │   ├── config.ts
│   │   │   └── home.spec.ts
│   │   ├── my-curriculum/
│   │   │   ├── config.ts
│   │   │   └── my-curriculum.spec.ts
│   │   └── ...
│   │
│   ├── utils/                              # ✨ 공용 유틸리티 (새로운 구조)
│   │   ├── browser-logger.ts               # 브라우저 로그 캡처
│   │   ├── test-helpers.ts                 # 자주 쓰는 헬퍼 함수
│   │   └── selectors.ts                    # 공용 선택자 모음
│   │
│   ├── shared/                             # ✨ 공유 설정 (새로운 구조)
│   │   └── test-config.ts                  # 전역 테스트 설정
│   │
│   ├── report-generator/                   # ✨ 리포트 생성 도구 (새로운 위치)
│   │   ├── generate-report.mjs
│   │   └── templates/
│   │       └── index.html
│   │
│   ├── README.md                           # ✨ 새로운 문서
│   └── (기존 파일들)                        # 이전 파일들은 사용 중단
│
├── playwright.config.ts                    # E2E 환경 설정
├── TESTING_STRUCTURE.md                    # 이 파일
└── FRONTEND_TESTING_GUIDE.md               # 기존 테스트 가이드
```

## ✨ 주요 개선 사항

### 1. **페이지별 폴더 구조**
- 각 페이지마다 독립적인 폴더 생성
- `config.ts`: URL, 선택자, 타임아웃 등을 한곳에서 관리
- `*.spec.ts`: 실제 테스트 로직

**장점:**
- ✅ 페이지별 테스트를 쉽게 찾을 수 있음
- ✅ 설정 변경 시 한 파일만 수정
- ✅ 새로운 페이지 테스트 추가가 간단
- ✅ 테스트 코드가 깔끔하고 가독성 높음

### 2. **공용 유틸리티 (`utils/`)**
- `test-helpers.ts`: 자주 사용하는 함수들
  - `navigateToPage()`: 페이지 이동
  - `captureConsoleErrors()`: 콘솔 에러 캡처
  - `assertElementVisible()`: 요소 확인
  - `runChecks()`: 여러 체크 실행
  - 등등...

- `browser-logger.ts`: 브라우저 로그 수집
  - 콘솔 메시지 캡처
  - 네트워크 에러 추적
  - JSON 내보내기

### 3. **공유 설정 (`shared/`)**
- `test-config.ts`: 모든 테스트에서 사용하는 공통 설정
  - 타임아웃 상수
  - 공용 선택자
  - 에러 필터링 규칙

**장점:**
- ✅ 중복 제거
- ✅ 설정 변경이 전체에 반영
- ✅ 테스트 유지보수 용이

### 4. **리포트 생성 도구 (`report-generator/`)**
- `generate-report.mjs`: 자동 테스트 리포트 생성
- 스크린샷, 콘솔 로그, 네트워크 요청 정보 포함

## 🧪 현재 테스트 상태

### 구조화된 페이지 테스트

| 페이지 | 테스트 파일 | 상태 | 테스트 수 |
|--------|----------|------|----------|
| GCP Settings | `e2e/pages/gcp-settings/gcp-settings.spec.ts` | ✅ PASS | 7 |
| Browse Curriculums | `e2e/pages/browse-curriculums/browse-curriculums.spec.ts` | ⏳ 수정 중 | 7 |
| Home | `e2e/pages/home/home.spec.ts` | ✅ PASS | 5 |
| My Curriculum | `e2e/pages/my-curriculum/my-curriculum.spec.ts` | ✅ PASS | 5 |

## 🚀 테스트 실행 방법

### 모든 페이지 테스트 실행
```bash
cd MATHESIS-LAB_FRONT
npx playwright test e2e/pages
```

### 특정 페이지만 테스트
```bash
# GCP Settings 페이지만
npx playwright test e2e/pages/gcp-settings

# Browse Curriculums 페이지만
npx playwright test e2e/pages/browse-curriculums
```

### UI 모드로 대화형 테스트
```bash
npx playwright test --ui e2e/pages
```

### 디버그 모드
```bash
npx playwright test --debug e2e/pages
```

## 📊 테스트 리포트 생성

```bash
# 새로운 구조에서 리포트 생성
node e2e/report-generator/generate-report.mjs

# 또는 기존 위치에서 (호환성 유지)
node e2e/generate-test-report.mjs
```

**생성되는 파일:**
- `test-report-with-logs/index.html` - HTML 리포트
- `test-report-with-logs/summary.json` - 테스트 요약
- `test-report-with-logs/screenshots/` - 페이지 스크린샷
- `test-report-with-logs/logs/` - 상세 로그 (JSON)

## 🔧 새로운 페이지 테스트 추가하기

### 1단계: 폴더 생성
```bash
mkdir e2e/pages/new-page-name
```

### 2단계: `config.ts` 생성
```typescript
// e2e/pages/new-page-name/config.ts
export const NEW_PAGE_CONFIG = {
  name: 'New Page',
  url: 'http://localhost:3002/#/new-page',

  selectors: {
    heading: 'h1',
    button: 'button:has-text("클릭")',
  },

  checks: [
    {
      selector: 'h1',
      expectVisible: true,
      description: '제목이 표시됨',
    },
  ],

  timeouts: {
    navigation: 15000,
    waitForElement: 5000,
  },

  expectedRequests: {
    min: 20,
    max: 60,
  },

  expectedErrors: 0,
};
```

### 3단계: 테스트 파일 생성
```typescript
// e2e/pages/new-page-name/new-page-name.spec.ts
import { test, expect } from '@playwright/test';
import { NEW_PAGE_CONFIG } from './config';

test.describe('New Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(NEW_PAGE_CONFIG.url, {
      waitUntil: 'networkidle',
      timeout: NEW_PAGE_CONFIG.timeouts.navigation,
    });
  });

  test('should display heading', async ({ page }) => {
    const heading = page.locator(NEW_PAGE_CONFIG.selectors.heading);
    await expect(heading).toBeVisible();
  });
});
```

## 📝 설정 파일 상세 설명

### `config.ts` 주요 속성

```typescript
export const PAGE_CONFIG = {
  // 페이지 이름 (리포트에 표시)
  name: 'Page Name',

  // 테스트할 URL
  url: 'http://localhost:3002/#/page',

  // 페이지 요소 선택자 (한곳에서 관리)
  selectors: {
    heading: 'h1',
    buttons: {
      submit: 'button:has-text("제출")',
      cancel: 'button:has-text("취소")',
    },
  },

  // 테스트 시 확인할 항목들
  checks: [
    {
      selector: 'h1',
      expectText: '페이지 제목',      // 텍스트 포함 확인
      expectVisible: true,             // 가시성 확인
      description: '제목 표시 확인',
    },
  ],

  // 타임아웃 설정
  timeouts: {
    navigation: 15000,    // 페이지 이동 타임아웃
    waitForElement: 5000, // 요소 대기 타임아웃
  },

  // 예상 네트워크 요청 수 범위
  expectedRequests: {
    min: 20,
    max: 60,
  },

  // 예상 콘솔 에러 수
  expectedErrors: 0,
};
```

## 🎯 Best Practices

### ✅ DO

1. **설정을 `config.ts`에 중앙화**
   ```typescript
   // ✅ Good
   const heading = page.locator(PAGE_CONFIG.selectors.heading);
   ```

2. **공용 헬퍼 함수 사용**
   ```typescript
   import { assertElementVisible, captureConsoleErrors } from '../../utils/test-helpers';

   // ✅ Good
   await assertElementVisible(page, PAGE_CONFIG.selectors.heading);
   ```

3. **타임아웃 설정에서 상수 사용**
   ```typescript
   // ✅ Good
   await page.goto(url, { timeout: PAGE_CONFIG.timeouts.navigation });
   ```

### ❌ DON'T

1. **선택자 하드코딩**
   ```typescript
   // ❌ Bad
   await page.locator('h1').click();

   // ✅ Good
   await page.locator(PAGE_CONFIG.selectors.heading).click();
   ```

2. **try-catch로 에러 숨기기**
   ```typescript
   // ❌ Bad - 에러가 숨겨짐
   try {
     await page.locator('selector').click();
   } catch (e) {}

   // ✅ Good - 명시적으로 처리
   await expect(page.locator('selector')).toBeVisible();
   ```

3. **하드코딩된 타임아웃**
   ```typescript
   // ❌ Bad
   await page.waitForTimeout(5000);

   // ✅ Good
   await page.waitForLoadState('networkidle');
   ```

## 📚 문서

- **`e2e/README.md`**: 상세 E2E 테스트 가이드
- **`FRONTEND_TESTING_GUIDE.md`**: 프론트엔드 테스트 전체 가이드
- **이 파일**: 구조 변경 내용 설명

## 🔄 마이그레이션 상태

### 완료된 작업 ✅
- [x] 페이지별 폴더 구조 생성
- [x] GCP Settings 페이지 테스트 구조화
- [x] Browse Curriculums 페이지 테스트 구조화
- [x] Home 페이지 테스트 추가
- [x] My Curriculum 페이지 테스트 추가
- [x] 공용 유틸리티 생성
- [x] 공유 설정 파일 생성
- [x] README 문서 작성

### 진행 중인 작업 ⏳
- [ ] Browse Curriculums 테스트 에러 수정
- [ ] 모든 테스트 통과 확인
- [ ] 기존 테스트 파일 정리

## 📈 앞으로의 개선 계획

1. **테스트 커버리지 확대**
   - Curriculum Editor 페이지 테스트
   - Node Editor 페이지 테스트
   - 인터랙션 테스트 추가

2. **시각적 회귀 테스트**
   - 스크린샷 비교 자동화
   - 레이아웃 변경 감지

3. **접근성 테스트**
   - ARIA 라벨 확인
   - 키보드 네비게이션 테스트

4. **성능 테스트**
   - 페이지 로드 시간 측정
   - 번들 크기 모니터링

## 🤝 기여하기

새로운 페이지 테스트를 추가할 때:
1. `e2e/pages/page-name/` 폴더 생성
2. `config.ts`와 `page-name.spec.ts` 파일 생성
3. `e2e/README.md`에 문서 추가
4. 모든 테스트 통과 확인

## 📞 문의 및 지원

- 테스트 구조에 대한 질문: `e2e/README.md` 참고
- 특정 페이지 테스트 추가: 위의 "새로운 페이지 테스트 추가하기" 섹션 참고

---

**마지막 업데이트:** 2025-11-17
**구조 버전:** v2.0 (페이지별 폴더 구조)
