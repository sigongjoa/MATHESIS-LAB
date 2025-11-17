# Google OAuth2 빠른 시작 (5분)

## 1. Google Cloud Console 열기
https://console.cloud.google.com

## 2. 프로젝트 선택
- 좌측 상단 **프로젝트 선택** 클릭
- **새 프로젝트** > 이름: `MATHESIS-LAB` > **만들기**

## 3. OAuth 동의 화면 설정 (한 번만)
1. 좌측 메뉴 > **API 및 서비스** > **OAuth 동의 화면**
2. **외부** 선택 > **만들기**
3. 앱 이름: `MATHESIS LAB`
4. 이메일: `yourname@gmail.com` (자신의 이메일)
5. **저장 후 계속** (범위 건너뛰기 가능)
6. **테스트 사용자** > **사용자 추가** > 자신의 Gmail 주소 입력
7. **저장 후 계속** > **대시보드로 돌아가기**

## 4. 클라이언트 ID 발급받기
1. 좌측 메뉴 > **API 및 서비스** > **자격증명**
2. **+ 자격증명 만들기** > **OAuth 2.0 클라이언트 ID**
3. **웹 애플리케이션** 선택
4. 이름: `MATHESIS LAB Frontend`

### 승인된 JavaScript 출처 추가:
```
http://localhost:3000
http://localhost:3002
```

### 승인된 리디렉션 URI 추가:
```
http://localhost:3000/auth/google/callback
http://localhost:3002/auth/google/callback
```

5. **만들기** 클릭
6. **팝업창에서 복사:**
   - 클라이언트 ID
   - 클라이언트 보안 비밀

## 5. .env 파일 설정
`backend/.env` 파일 열기:

```bash
GOOGLE_OAUTH_CLIENT_ID=여기_클라이언트_ID_붙이기
GOOGLE_OAUTH_CLIENT_SECRET=여기_클라이언트_비밀_붙이기
JWT_SECRET_KEY=아무거나_32글자이상_입력
```

## 6. 백엔드 시작
```bash
cd /mnt/d/progress/MATHESIS\ LAB
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload --port 8000
```

## 7. 테스트
```bash
curl "http://localhost:8000/api/v1/auth/google/auth-url?redirect_uri=http://localhost:3000/auth/google/callback"
```

## ✅ 완료!
Google OAuth2 구성이 완료되었습니다.

다음 단계: 프론트엔드 구글 로그인 버튼 구현

## 🆘 문제 해결

| 오류 | 원인 | 해결 |
|------|------|------|
| Invalid client_id | 잘못된 클라이언트 ID | `.env` 파일의 ID 확인 |
| redirect_uri does not match | 리디렉션 URI 불일치 | Google Cloud에서 정확히 등록 |
| CORS error | JavaScript 출처 미등록 | `http://localhost:3000` 등 추가 |
| "등록되지 않은 앱" 경고 | 정상 (개발 앱) | **고급** > **계속** 클릭 |

