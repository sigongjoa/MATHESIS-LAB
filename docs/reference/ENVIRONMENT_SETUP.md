# 환경변수 설정 가이드

이 문서는 MATHESIS LAB 프로젝트의 환경변수 설정 방법을 설명합니다.

## 🔒 보안 원칙

**절대 금지:**
- 민감한 데이터(API 키, 비밀번호 등)를 코드에 하드코딩하기
- 민감한 데이터를 Git에 커밋하기
- 개인 자격증명을 공유하기

**권장 사항:**
- 모든 민감한 데이터는 `.env` 또는 `.env.local` 파일에 저장
- `.env.local` 파일은 Git에서 제외 (`.gitignore` 설정됨)
- `.env.example` 또는 `.env.local.example` 파일로 필수 변수 문서화

---

## 📝 백엔드 환경변수 설정

### 파일 위치
```
backend/.env          # 실제 자격증명 (Git 제외)
backend/.env.example  # 템플릿 (Git 포함)
```

### 설정 방법

1. **예제 파일 확인**
   ```bash
   cat backend/.env.example
   ```

2. **로컬 설정 파일 생성**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **당신의 자격증명으로 수정**
   ```bash
   # backend/.env
   GOOGLE_OAUTH_CLIENT_ID=your-actual-client-id
   GOOGLE_OAUTH_CLIENT_SECRET=your-actual-secret
   ```

### 필수 환경변수

| 변수명 | 설명 | 필수 | 예시 |
|--------|------|------|------|
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth 클라이언트 ID | ❌ | `533847210806-...apps.googleusercontent.com` |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth 클라이언트 시크릿 | ❌ | `GOCSPX-...` |
| `DATABASE_URL` | 데이터베이스 연결 문자열 | ✅ | `sqlite:///./mathesis_lab.db` |
| `JWT_SECRET_KEY` | JWT 서명용 비밀키 | ✅ | (보안 무작위 문자열) |

### 선택 환경변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `VERTEX_AI_PROJECT_ID` | Google Vertex AI 프로젝트 ID | (미설정) |
| `VERTEX_AI_LOCATION` | Vertex AI 리전 | `us-central1` |
| `ENABLE_AI_FEATURES` | AI 기능 활성화 | `False` |
| `YOUTUBE_API_KEY` | YouTube Data API 키 | (미설정) |
| `ZOTERO_API_KEY` | Zotero API 키 | (미설정) |

---

## 🎨 프론트엔드 환경변수 설정

### 파일 위치
```
MATHESIS-LAB_FRONT/.env.local       # 실제 자격증명 (Git 제외)
MATHESIS-LAB_FRONT/.env.local.example # 템플릿 (Git 포함)
```

### 설정 방법

1. **예제 파일 확인**
   ```bash
   cat MATHESIS-LAB_FRONT/.env.local.example
   ```

2. **로컬 설정 파일 생성**
   ```bash
   cp MATHESIS-LAB_FRONT/.env.local.example MATHESIS-LAB_FRONT/.env.local
   ```

3. **당신의 자격증명으로 수정**
   ```bash
   # MATHESIS-LAB_FRONT/.env.local
   REACT_APP_GOOGLE_CLIENT_ID=your-actual-client-id
   ```

### 필수 환경변수

| 변수명 | 설명 | 필수 | 예시 |
|--------|------|------|------|
| `REACT_APP_GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID (프론트엔드용) | ❌ | `533847210806-...apps.googleusercontent.com` |
| `VITE_API_URL` | 백엔드 API 기본 URL | ✅ | `/api/v1` |

---

## 🔐 Google OAuth 자격증명 발급 방법

### 1단계: Google Cloud Console 접속
- https://console.cloud.google.com/ 방문
- 프로젝트 생성 또는 선택

### 2단계: OAuth 동의 화면 구성
- 좌측 메뉴 → "OAuth 동의 화면"
- 사용자 유형: "외부" 선택
- 필수 정보 입력

### 3단계: OAuth 클라이언트 ID 생성
- 좌측 메뉴 → "사용자 인증 정보"
- "사용자 인증 정보 만들기" → "OAuth 2.0 클라이언트 ID"
- 애플리케이션 유형: "웹 애플리케이션"
- 승인된 리디렉션 URI:
  ```
  http://localhost:3000/auth/callback
  http://localhost:3002/auth/callback
  https://your-domain.com/auth/callback
  ```

### 4단계: 자격증명 다운로드/복사
- JSON 다운로드 또는 클라이언트 ID/시크릿 복사
- `.env` 파일에 추가

---

## ✅ 검증 체크리스트

### 백엔드 환경변수 확인
```bash
# backend/.env 파일이 존재하는지 확인
[ -f backend/.env ] && echo "✅ backend/.env 존재" || echo "❌ backend/.env 없음"

# 필수 변수가 설정되어 있는지 확인
grep -q "DATABASE_URL" backend/.env && echo "✅ DATABASE_URL 설정됨" || echo "❌ DATABASE_URL 미설정"
grep -q "JWT_SECRET_KEY" backend/.env && echo "✅ JWT_SECRET_KEY 설정됨" || echo "❌ JWT_SECRET_KEY 미설정"
```

### 프론트엔드 환경변수 확인
```bash
# .env.local 파일이 존재하는지 확인
[ -f MATHESIS-LAB_FRONT/.env.local ] && echo "✅ .env.local 존재" || echo "❌ .env.local 없음"

# REACT_APP_GOOGLE_CLIENT_ID 설정 확인
grep -q "REACT_APP_GOOGLE_CLIENT_ID" MATHESIS-LAB_FRONT/.env.local && echo "✅ REACT_APP_GOOGLE_CLIENT_ID 설정됨" || echo "❌ REACT_APP_GOOGLE_CLIENT_ID 미설정"
```

---

## 🚀 개발 시작하기

### 1단계: 환경변수 설정
```bash
# 백엔드
cp backend/.env.example backend/.env
# backend/.env 편집하여 실제 값 입력

# 프론트엔드
cp MATHESIS-LAB_FRONT/.env.local.example MATHESIS-LAB_FRONT/.env.local
# MATHESIS-LAB_FRONT/.env.local 편집하여 실제 값 입력
```

### 2단계: 의존성 설치
```bash
# 백엔드
cd backend
pip install -r requirements.txt

# 프론트엔드
cd MATHESIS-LAB_FRONT
npm install
```

### 3단계: 서버 실행
```bash
# 백엔드 (터미널 1)
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 (터미널 2)
cd MATHESIS-LAB_FRONT
npm run dev
```

---

## 🔍 문제 해결

### Google 로그인이 작동하지 않을 때
1. `REACT_APP_GOOGLE_CLIENT_ID`가 설정되어 있는지 확인
2. Google Cloud Console에서 클라이언트 ID 확인
3. 브라우저 개발자 도구 → 콘솔에서 에러 메시지 확인
4. Google Cloud Console에서 리디렉션 URI 확인

### API 호출 실패 시
1. 백엔드 서버가 실행 중인지 확인 (포트 8000)
2. `VITE_API_URL` 환경변수 확인
3. 백엔드 로그에서 에러 메시지 확인
4. CORS 설정 확인 (backend/.env의 `ALLOWED_ORIGINS`)

### 데이터베이스 에러 시
1. `DATABASE_URL` 환경변수 확인
2. 데이터베이스 파일 권한 확인
3. `python -m alembic upgrade head` 마이그레이션 실행

---

## 📚 참고

- [Google OAuth 2.0 문서](https://developers.google.com/identity/protocols/oauth2)
- [Vertex AI 문서](https://cloud.google.com/vertex-ai/docs)
- [FastAPI 환경변수](https://fastapi.tiangolo.com/advanced/settings/)
- [Vite 환경변수](https://vitejs.dev/guide/env-and-mode.html)

---

**마지막 업데이트**: 2025-11-17
**작성자**: Claude Code
