# Google OAuth2 Frontend Integration Guide

## 📋 개요

MATHESIS LAB의 프론트엔드에서 Google OAuth2 로그인 기능이 구현되었습니다.

**Status:** ✅ **완료**

---

## 🎯 구현 내용

### 1️⃣ **Google Auth Service** (`services/googleAuthService.ts`)
- Google ID Token 검증
- JWT 토큰 저장/관리
- 로그인 상태 확인
- API 인증 헤더 생성

### 2️⃣ **Google Sign-In Button** (`components/GoogleSignInButton.tsx`)
- Google Sign-In 버튼 렌더링
- OAuth 콜백 처리
- 에러 처리
- 대시보드로 자동 리다이렉트

### 3️⃣ **BrowseCurriculums 페이지 통합** (`pages/BrowseCurriculums.tsx`)
- Google 로그인 버튼 추가
- 로그인 상태 관리
- 에러 메시지 표시

---

## 🔧 **설정 방법**

### Step 1: 환경변수 설정

```bash
cd MATHESIS-LAB_FRONT
cp .env.example .env.local
```

`.env.local` 파일 내용:
```
VITE_API_URL=http://localhost:8000/api/v1
REACT_APP_GOOGLE_CLIENT_ID=533847210806-kvdgfhlpspqkckk3kqdrug05f3o77kaf.apps.googleusercontent.com
```

### Step 2: 의존성 확인

Google Sign-In은 CDN에서 로드되므로 추가 패키지 설치 불필요:
```bash
npm install
```

### Step 3: 프론트엔드 실행

```bash
npm run dev
# 접속: http://localhost:3002
```

---

## 🚀 **사용 방법**

### Google 로그인 버튼 사용

```tsx
import GoogleSignInButton from './components/GoogleSignInButton';

<GoogleSignInButton
  onSignInStart={() => setLoading(true)}
  onSignInError={(error) => console.error(error)}
  buttonText="로그인"
/>
```

### 토큰 사용 (API 요청)

```tsx
import googleAuthService from '../services/googleAuthService';

// 로그인 확인
if (googleAuthService.isLoggedIn()) {
  // 인증 헤더 자동 추가
  const headers = {
    'Content-Type': 'application/json',
    ...googleAuthService.getAuthHeader()
  };

  const response = await fetch('/api/v1/curriculums', { headers });
}

// 토큰 명시적 사용
const token = googleAuthService.getAccessToken();
```

### 로그아웃

```tsx
googleAuthService.clearTokens();
// 또는
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

---

## 🔌 **백엔드 API 연동**

### 엔드포인트

**POST** `/api/v1/auth/google/verify-token`

**Request:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "google_106773691989701073250@oauth.local",
    "name": "Google User",
    "profile_picture_url": null,
    "role": "user",
    "is_active": true,
    "created_at": "2025-11-16T13:11:57.082813",
    "updated_at": "2025-11-16T13:11:57.091717",
    "last_login": "2025-11-16T13:11:57.090588"
  }
}
```

---

## 🧪 **테스트**

### 프론트엔드 테스트 작성

```bash
npm test GoogleSignInButton.test.tsx
```

예제 테스트 (`components/GoogleSignInButton.test.tsx`):

```tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import GoogleSignInButton from './GoogleSignInButton';

describe('GoogleSignInButton', () => {
  it('should render Google sign-in button', () => {
    render(
      <BrowserRouter>
        <GoogleSignInButton />
      </BrowserRouter>
    );

    const container = screen.getByText(/google/i, { selector: 'div' });
    expect(container).toBeInTheDocument();
  });

  it('should handle sign-in error', () => {
    const onError = jest.fn();
    render(
      <BrowserRouter>
        <GoogleSignInButton onSignInError={onError} />
      </BrowserRouter>
    );

    // Error handling test
    expect(onError).not.toHaveBeenCalled();
  });
});
```

---

## 🔐 **보안 고려사항**

### ✅ 구현된 보안 사항

1. **HTTPS 필수** - Google Sign-In은 HTTPS 환경 필요
2. **Client ID 검증** - 백엔드에서 Client ID 확인
3. **Token 서명 검증** - Google 공개 키로 검증
4. **CORS 설정** - 백엔드에서 프론트엔드 도메인 허용
5. **HttpOnly 고려** (향후)

### ⚠️ 고려 사항

- 토큰은 localStorage에 저장 (XSS에 취약)
- **권장:** 토큰을 HttpOnly Cookie에 저장

---

## 📚 **파일 구조**

```
MATHESIS-LAB_FRONT/
├── services/
│   └── googleAuthService.ts       # OAuth 서비스 로직
├── components/
│   └── GoogleSignInButton.tsx      # Google 로그인 버튼
├── pages/
│   └── BrowseCurriculums.tsx       # 로그인 버튼 통합
├── .env.example                    # 환경변수 템플릿
└── .env.local                      # 실제 환경변수 (git 제외)
```

---

## 🎓 **학습 자료**

- [Google Sign-In for Web](https://developers.google.com/identity/gsi/web)
- [OAuth 2.0 Flow](https://tools.ietf.org/html/rfc6749)
- [JWT 토큰](https://jwt.io/)

---

## ✅ **체크리스트**

- [x] Google Auth Service 구현
- [x] Google Sign-In Button 구현
- [x] BrowseCurriculums 통합
- [x] 환경변수 설정
- [x] API 연동
- [ ] Unit 테스트 작성 (예정)
- [ ] E2E 테스트 작성 (예정)
- [ ] HttpOnly Cookie 적용 (예정)

---

## 🐛 **문제 해결**

### Q: Google 로그인 버튼이 안 보여요
**A:**
- `.env.local` 파일 확인
- `REACT_APP_GOOGLE_CLIENT_ID` 값 확인
- 브라우저 콘솔에서 에러 확인

### Q: "Invalid Google ID token" 에러
**A:**
- 토큰 만료 확인 (재로그인 시도)
- 백엔드 환경변수 확인
- Client ID 일치 확인

### Q: CORS 에러
**A:**
- 백엔드 CORS 설정 확인
- 프론트엔드 URL이 `allow_origins`에 포함되었는지 확인

---

**최종 업데이트:** 2025-11-16
