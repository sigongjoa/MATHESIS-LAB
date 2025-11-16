# Google OAuth2 클라이언트 ID/Secret 발급받기 가이드

## 1단계: Google Cloud 프로젝트 생성

### 1.1 Google Cloud Console 접속
1. https://console.cloud.google.com 에 접속
2. Google 계정으로 로그인

### 1.2 새 프로젝트 생성
```
상단 좌측 "프로젝트 선택" 클릭
→ "새 프로젝트" 클릭
→ 프로젝트 이름: MATHESIS-LAB (또는 원하는 이름)
→ 조직: 비워두기 (개인 개발)
→ "만들기" 클릭
```

프로젝트 생성에 30초~1분 걸립니다.

---

## 2단계: Google OAuth2 API 활성화

### 2.1 API 라이브러리 접속
1. 좌측 메뉴 > **API 및 서비스** > **라이브러리**
2. 검색창에 **"Google+ API"** 또는 **"OAuth"** 검색
3. **"Google+ API"** 클릭
4. **"활성화"** 버튼 클릭

### 2.2 OAuth 동의 화면 설정
1. 좌측 메뉴 > **API 및 서비스** > **OAuth 동의 화면**
2. **사용자 유형 선택**:
   - 개인 개발: **외부** 선택
   - 회사 개발: **내부** 선택
3. **만들기** 클릭

### 2.3 OAuth 동의 화면 양식 작성

**앱 정보:**
```
앱 이름: MATHESIS LAB
사용자 지원 이메일: your-email@gmail.com (자신의 Google 계정)
```

**개발자 연락처 정보:**
```
이메일: your-email@gmail.com
```

**저장 후 계속** 클릭

### 2.4 범위(Scopes) 추가
1. **범위 추가 또는 제거** 클릭
2. 다음 범위 검색해서 추가:
   - `openid`
   - `email`
   - `profile`
3. **업데이트** > **저장 후 계속** 클릭

### 2.5 테스트 사용자 추가
1. **테스트 사용자** 섹션
2. **사용자 추가** 클릭
3. Google 계정 이메일 주소 입력 (자신의 Gmail)
4. **추가** 클릭
5. **저장 후 계속** > **대시보드로 돌아가기**

---

## 3단계: OAuth2 자격증명(Credentials) 생성

### 3.1 자격증명 페이지 이동
1. 좌측 메뉴 > **API 및 서비스** > **자격증명**

### 3.2 OAuth2 클라이언트 ID 생성
1. **+ 자격증명 만들기** 클릭
2. **OAuth 2.0 클라이언트 ID** 선택

### 3.3 애플리케이션 유형 선택
```
애플리케이션 유형: 웹 애플리케이션
이름: MATHESIS LAB Frontend (또는 원하는 이름)
```

### 3.4 승인된 JavaScript 출처 추가
**승인된 JavaScript 출처** 섹션에 다음 추가:

개발 환경:
```
http://localhost:3000
http://localhost:3002
```

프로덕션 환경 (나중에 추가):
```
https://yourdomain.com
```

### 3.5 승인된 리디렉션 URI 추가
**승인된 리디렉션 URI** 섹션에 다음 추가:

개발 환경:
```
http://localhost:3000/auth/google/callback
http://localhost:3002/auth/google/callback
```

프로덕션 환경 (나중에 추가):
```
https://yourdomain.com/auth/google/callback
```

### 3.6 클라이언트 ID와 Secret 확인
1. **만들기** 클릭
2. 팝업창에 다음이 표시됨:
   - **클라이언트 ID** (복사!)
   - **클라이언트 보안 비밀** (복사!)

---

## 4단계: .env 파일 설정

### 4.1 `.env` 파일 열기
`backend/.env` 파일을 텍스트 에디터로 열기

### 4.2 값 입력
```bash
# Google OAuth2 Configuration
GOOGLE_OAUTH_CLIENT_ID=앞에서_복사한_클라이언트_ID
GOOGLE_OAUTH_CLIENT_SECRET=앞에서_복사한_클라이언트_보안_비밀
```

**예:**
```bash
GOOGLE_OAUTH_CLIENT_ID=123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxx
```

### 4.3 JWT_SECRET_KEY 설정 (선택)
```bash
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
```

32글자 이상의 아무 문자열 가능 (개발용이므로 간단해도 됨)

---

## 5단계: 백엔드 서버 시작

### 5.1 터미널에서 백엔드 시작
```bash
cd /mnt/d/progress/MATHESIS\ LAB
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload --port 8000
```

### 5.2 API 확인
브라우저에서 http://localhost:8000/docs 방문
- `GET /api/v1/auth/google/auth-url` 엔드포인트 확인

---

## 6단계: 테스트

### 6.1 Authorization URL 생성 테스트
```bash
curl "http://localhost:8000/api/v1/auth/google/auth-url?redirect_uri=http://localhost:3000/auth/google/callback"
```

응답 예:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=123456789-abc.apps.googleusercontent.com&redirect_uri=http://localhost:3000/auth/google/callback&response_type=code&scope=openid+email+profile"
}
```

### 6.2 프론트엔드에서 테스트 (나중에)
구글 로그인 버튼 클릭 → Google 로그인 페이지 표시 → 성공!

---

## 문제 해결

### 문제 1: "Invalid client_id" 오류
**원인:** `.env` 파일의 클라이언트 ID가 잘못됨

**해결:**
1. Google Cloud Console 다시 확인
2. 정확한 클라이언트 ID 복사
3. `.env` 파일 수정
4. 백엔드 재시작

### 문제 2: "The redirect_uri does not match" 오류
**원인:** 등록된 리디렉션 URI와 실제 리디렉션 URI가 다름

**해결:**
1. Google Cloud Console > 자격증명
2. OAuth2 클라이언트 ID 수정
3. 리디렉션 URI 확인:
   - 정확히 `http://localhost:3000/auth/google/callback` 인지 확인
   - 대소문자, `/` 등이 정확히 일치해야 함

### 문제 3: CORS 오류
**원인:** 승인된 JavaScript 출처가 없음

**해결:**
1. Google Cloud Console > 자격증명
2. OAuth2 클라이언트 ID 수정
3. "승인된 JavaScript 출처"에 다음 추가:
   - `http://localhost:3000`
   - `http://localhost:3002`

### 문제 4: "등록되지 않은 앱입니다" 경고
**해결:** 정상입니다! 개발 앱이기 때문
- **고급** > **MATHESIS LAB로 이동** 클릭
- "등록되지 않은 앱입니다. 이 앱의 소유자를 신뢰하나요?" > **계속** 클릭

---

## 프로덕션 배포 준비

### 보안 체크리스트
- [ ] JWT_SECRET_KEY를 32글자 이상 복잡한 문자열로 변경
- [ ] `.env` 파일을 버전 관리(git)에서 제외 (.gitignore)
- [ ] 클라이언트 ID/Secret을 환경 변수로 관리
- [ ] HTTPS 사용
- [ ] 리디렉션 URI를 프로덕션 도메인으로 변경

### 프로덕션 설정 변경
```bash
# Google Cloud Console에서:
# 1. 새 OAuth2 자격증명 생성 (프로덕션용)
# 2. 리디렉션 URI를 프로덕션 도메인으로 설정:
#    https://yourdomain.com/auth/google/callback
# 3. JavaScript 출처:
#    https://yourdomain.com

# .env 파일 업데이트:
GOOGLE_OAUTH_CLIENT_ID=프로덕션_클라이언트_ID
GOOGLE_OAUTH_CLIENT_SECRET=프로덕션_클라이언트_SECRET
```

---

## 유용한 링크

- [Google Cloud Console](https://console.cloud.google.com)
- [Google OAuth2 문서](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In 문서](https://developers.google.com/identity/gsi/web)

---

## 다음 단계

1. ✅ 클라이언트 ID/Secret 발급 완료
2. ⬜ 프론트엔드 Google Sign-In 버튼 구현
3. ⬜ OAuth2 콜백 페이지 구현
4. ⬜ 통합 테스트
5. ⬜ 프로덕션 배포

