# E2E Test Structure

MATHESIS LAB 프론트엔드 E2E 테스트 구조 및 사용 설명서

## 📁 폴더 구조

```
e2e/
├── pages/                              # 페이지별 테스트 폴더
│   ├── gcp-settings/
│   │   ├── gcp-settings.spec.ts       # GCP Settings 페이지 테스트
│   │   └── config.ts                  # 페이지 테스트 설정 (URL, 셀렉터 등)
│   ├── browse-curriculums/
│   │   ├── browse-curriculums.spec.ts
│   │   └── config.ts
│   ├── my-curriculum/
│   │   ├── my-curriculum.spec.ts
│   │   └── config.ts
│   └── home/
│       ├── home.spec.ts
│       └── config.ts
├── utils/                              # 공통 유틸리티
│   ├── browser-logger.ts              # 브라우저 로그 캡처
│   ├── test-helpers.ts                # 테스트 헬퍼 함수
│   └── selectors.ts                   # 공용 선택자
├── shared/                             # 공유 설정
│   ├── test-config.ts                 # 공통 테스트 설정
│   └── constants.ts                   # 공통 상수
├── report-generator/                   # 리포트 생성 도구
│   ├── generate-report.mjs            # 테스트 리포트 생성 스크립트
│   └── templates/
│       └── index.html                  # HTML 리포트 템플릿
└── README.md                           # 이 파일
```

## 🎯 페이지별 테스트 구조

### GCP Settings 페이지 (`pages/gcp-settings/`)

**테스트 파일**: `gcp-settings.spec.ts`

**설정**: `config.ts`에서 다음을 정의:
- URL: `http://localhost:3002/#/gcp-settings`
- Selectors: 페이지 요소 선택자 (탭, 버튼, 제목 등)
- Checks: 테스트 시 확인할 항목들
- Timeouts: 타임아웃 설정
- Expected Requests: 예상 네트워크 요청 수

**테스트 항목**:
- ✅ 페이지 제목 및 부제목 표시 확인
- ✅ 탭 버튼 표시 확인 (Overview, Backup, Sync)
- ✅ GCP Integration Status 섹션 표시 확인
- ✅ Available Features 섹션 표시 확인
- ✅ 액션 버튼 표시 확인 (Refresh, Health Check)
- ✅ 콘솔 에러 없음 확인
- ✅ 탭 전환 기능 확인

### Browse Curriculums 페이지 (`pages/browse-curriculums/`)

**테스트 파일**: `browse-curriculums.spec.ts`

**설정**: `config.ts`에서 다음을 정의:
- URL: `http://localhost:3002/#/browse`
- Selectors: 검색 입력, 커리큘럼 카드, 로그인 버튼 등
- Expected Errors: GSI 인증 에러는 개발 환경에서 발생 가능

### Home (My Curriculum) 페이지 (`pages/home/`)

**테스트 파일**: `home.spec.ts`

**설정**: `config.ts`에서 다음을 정의:
- URL: `http://localhost:3002/`
- 페이지 제목, 네비게이션, 버튼 등의 요소 선택자

### My Curriculum 페이지 (`pages/my-curriculum/`)

**테스트 파일**: `my-curriculum.spec.ts`

**설정**: `config.ts`에서 다음을 정의:
- 커리큘럼 목록, 생성 버튼, 모달 등의 요소 선택자

## 🛠️ 공유 유틸리티

### Shared Config (`shared/test-config.ts`)

모든 테스트에서 사용하는 공통 설정:
- **COMMON_TIMEOUTS**: 각 작업별 타임아웃 설정
- **COMMON_SELECTORS**: 자주 사용하는 요소 선택자
- **TEST_CONFIG**: 테스트 환경 설정
- **Helper Functions**: 콘솔 에러, 네트워크 에러 필터링

### Test Helpers (`utils/test-helpers.ts`)

자주 사용하는 유틸리티 함수:
- `navigateToPage()`: 페이지 네비게이션
- `captureConsoleErrors()`: 콘솔 에러 캡처
- `assertElementVisible()`: 요소 가시성 확인
- `captureNetworkStats()`: 네트워크 통계 수집
- `runChecks()`: 여러 체크 항목 실행
- `takeScreenshot()`: 스크린샷 캡처

### Browser Logger (`utils/browser-logger.ts`)

브라우저 콘솔 및 네트워크 에러 로깅:
- 콘솔 메시지 캡처 (log, warn, error)
- 네트워크 에러 캡처 (4xx, 5xx)
- 타임스탬프 및 위치 정보 포함
- JSON 내보내기 기능

## 📊 테스트 실행

### 모든 E2E 테스트 실행

```bash
cd MATHESIS-LAB_FRONT
npx playwright test e2e/pages
```

### 특정 페이지 테스트 실행

```bash
# GCP Settings 페이지
npx playwright test e2e/pages/gcp-settings

# Browse Curriculums 페이지
npx playwright test e2e/pages/browse-curriculums

# Home 페이지
npx playwright test e2e/pages/home
```

### UI 모드로 테스트 실행 (권장)

```bash
npx playwright test --ui e2e/pages
```

### 디버그 모드로 테스트 실행

```bash
npx playwright test --debug e2e/pages
```

## 📈 테스트 리포트 생성

### 테스트 리포트 자동 생성

```bash
cd MATHESIS-LAB_FRONT
node e2e/report-generator/generate-report.mjs
```

### 생성된 리포트 확인

```bash
# Linux / WSL
xdg-open test-report-with-logs/index.html

# macOS
open test-report-with-logs/index.html

# Windows
start test-report-with-logs/index.html
```

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
    button: 'button',
  },
  checks: [
    {
      selector: 'h1',
      expectVisible: true,
      description: 'Heading is visible',
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

  test('should display page heading', async ({ page }) => {
    const heading = page.locator(NEW_PAGE_CONFIG.selectors.heading);
    await expect(heading).toBeVisible();
  });
});
```

## 💡 모범 사례

### ✅ DO

1. **페이지별로 폴더 구성**
   ```
   e2e/pages/page-name/
   ├── config.ts
   └── page-name.spec.ts
   ```

2. **설정을 `config.ts`에 중앙화**
   - URL, 선택자, 타임아웃을 한 곳에서 관리
   - 변경 시 한 곳에서만 수정

3. **설명적인 테스트 이름 사용**
   ```typescript
   test('should display GCP Settings page heading and main layout', async ({ page }) => {
     // ...
   });
   ```

4. **공용 헬퍼 함수 사용**
   ```typescript
   import { assertElementVisible, captureConsoleErrors } from '../../utils/test-helpers';
   ```

5. **콘솔 에러 필터링**
   ```typescript
   const criticalErrors = errors.filter(
     (error) => !error.includes('cdn.tailwindcss.com')
   );
   ```

### ❌ DON'T

1. **하드코딩된 선택자**
   ```typescript
   // ❌ 나쁜 예
   await page.locator('button').click();

   // ✅ 좋은 예
   await page.locator(GCP_SETTINGS_CONFIG.selectors.buttons.refresh).click();
   ```

2. **하드코딩된 타임아웃**
   ```typescript
   // ❌ 나쁜 예
   await page.waitForTimeout(5000);

   // ✅ 좋은 예
   await page.waitForLoadState('networkidle', { timeout: GCP_SETTINGS_CONFIG.timeouts.navigation });
   ```

3. **try-catch 블록 사용** (에러 숨김)
   ```typescript
   // ❌ 나쁜 예
   try {
     await page.locator('selector').click();
   } catch (e) {
     // 에러가 숨겨짐
   }

   // ✅ 좋은 예
   await expect(page.locator('selector')).toBeVisible();
   await page.locator('selector').click();
   ```

4. **테스트 간의 의존성 만들기**
   ```typescript
   // ❌ 나쁜 예: 첫 번째 테스트의 결과에 의존
   test('should create curriculum', async ({ page }) => {
     // ... 생성 로직
   });

   test('should edit curriculum', async ({ page }) => {
     // 이 테스트는 위 테스트가 통과했다고 가정
   });

   // ✅ 좋은 예: 각 테스트는 독립적
   test('should create curriculum', async ({ page }) => {
     // 독립적인 테스트
   });

   test('should edit curriculum', async ({ page }) => {
     // 독립적인 테스트
   });
   ```

## 🐛 문제 해결

### 테스트가 타임아웃되는 경우

```bash
# 디버그 모드로 실행
npx playwright test --debug e2e/pages

# 또는 UI 모드로 실행
npx playwright test --ui e2e/pages
```

### 선택자를 찾을 수 없는 경우

1. 브라우저 콘솔에서 선택자 테스트
2. Playwright Inspector 사용
3. `config.ts`의 선택자 확인

### 콘솔 에러로 인한 테스트 실패

1. `shared/test-config.ts`의 `ignoreConsoleErrors` 배열에 패턴 추가
2. 실제 에러인 경우 코드 수정

## 📚 참고 자료

- [Playwright 공식 문서](https://playwright.dev/)
- [Playwright 최고의 관행](https://playwright.dev/docs/best-practices)
- [테스트 선택자 생성](https://playwright.dev/docs/locators)
- [디버깅](https://playwright.dev/docs/debug)

## 📝 버전 이력

- **v1.0** (2025-11-17): 초기 구조화
  - 페이지별 폴더 구조 도입
  - 공유 설정 및 유틸리티 생성
  - GCP Settings, Browse Curriculums, Home, My Curriculum 페이지 테스트 추가

## 🤝 기여 가이드

새로운 페이지 테스트를 추가할 때:

1. 위의 "새로운 페이지 테스트 추가하기" 섹션 참고
2. 모범 사례 준수
3. 모든 테스트가 통과하는지 확인
4. 이 README에 페이지 테스트 문서 추가
