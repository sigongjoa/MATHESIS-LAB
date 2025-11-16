# MATHESIS LAB 웹 배포 + JWT 인증 + GCP 연동 - 구현 계획

## 📊 전체 일정 및 작업 분해

### 총 예상 기간: 4-5주

```
Week 1: JWT 인증 시스템 기초 구축
Week 2: GCP 연동 및 컨테이너화
Week 3: 배포 자동화 및 테스트
Week 4: 모크업 배포 및 검증
Week 5: 최종 테스트 및 운영 준비
```

---

## Phase 1: JWT 인증 시스템 (7일)

### 1.1 백엔드 - 인증 기초 구현

#### 작업 1: JWT 토큰 핸들러 생성
**File**: `backend/app/auth/jwt_handler.py`

```python
# 요구사항:
- JWT 생성/검증 로직
- Access Token (15분) 및 Refresh Token (7일) 생성
- 토큰 서명 (HS256)
- 토큰 검증 및 클레임 추출
- 토큰 만료 확인
- 비밀키 환경변수에서 로드
```

**테스트**:
```bash
pytest backend/tests/unit/test_jwt_handler.py
```

#### 작업 2: 비밀번호 처리
**File**: `backend/app/auth/password_handler.py`

```python
# 요구사항:
- bcrypt를 이용한 비밀번호 해싱
- 비밀번호 검증
- 강력한 비밀번호 검증 규칙
```

#### 작업 3: User 모델 생성
**File**: `backend/app/models/user.py`

```python
# SQLAlchemy 모델
class User(Base):
    user_id: str (UUID, PK)
    email: str (Unique)
    name: str
    password_hash: str (nullable)
    profile_picture_url: str (nullable)
    role: str (default: 'user')
    is_active: bool
    last_login: datetime
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime (soft delete)

    # 관계
    sessions: List[UserSession]
    curriculums: List[Curriculum]
```

#### 작업 4: 인증 스키마
**File**: `backend/app/schemas/auth.py`

```python
# 요구사항:
- LoginRequest (email, password)
- RegisterRequest (email, name, password)
- TokenResponse (access_token, refresh_token, expires_in)
- UserResponse (user_id, email, name, role)
- RefreshTokenRequest (refresh_token)
```

#### 작업 5: 인증 서비스
**File**: `backend/app/services/auth_service.py`

```python
# 요구사항:
class AuthService:
    - register(email, name, password) -> User
    - login(email, password) -> (access_token, refresh_token, user)
    - refresh_token(refresh_token) -> (new_access_token, new_refresh_token)
    - logout(user_id, refresh_token)
    - verify_token(token) -> claims
    - validate_password_strength(password)
```

#### 작업 6: 인증 엔드포인트
**File**: `backend/app/api/v1/endpoints/auth.py`

```python
# 엔드포인트:
POST   /api/v1/auth/register      # 회원가입
POST   /api/v1/auth/login         # 로그인
POST   /api/v1/auth/refresh       # 토큰 갱신
POST   /api/v1/auth/logout        # 로그아웃
GET    /api/v1/auth/me            # 현재 사용자 정보
```

#### 작업 7: 인증 의존성
**File**: `backend/app/core/dependencies.py`

```python
# 요구사항:
async def get_current_user(token: str) -> User
    - Authorization 헤더에서 토큰 추출
    - 토큰 검증
    - 사용자 조회
    - 활성 사용자 확인

# 사용:
@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    ...
```

#### 작업 8: 단위 테스트
**File**: `backend/tests/unit/test_auth_service.py`

```python
# 테스트 케이스:
- test_register_new_user
- test_register_duplicate_email
- test_login_success
- test_login_wrong_password
- test_login_nonexistent_user
- test_refresh_token
- test_invalid_token
- test_expired_token
- test_password_validation
- (목표: 95% 커버리지)
```

#### 작업 9: 통합 테스트
**File**: `backend/tests/integration/test_auth_api.py`

```python
# 테스트 케이스:
- test_register_endpoint
- test_login_endpoint
- test_refresh_endpoint
- test_logout_endpoint
- test_protected_endpoint_with_token
- test_protected_endpoint_without_token
- test_protected_endpoint_with_invalid_token
```

### 1.2 프론트엔드 - 인증 구현

#### 작업 10: 인증 서비스 (API 클라이언트)
**File**: `MATHESIS-LAB_FRONT/services/authService.ts`

```typescript
class AuthService {
    register(email: string, name: string, password: string): Promise<AuthResponse>
    login(email: string, password: string): Promise<AuthResponse>
    refresh(refreshToken: string): Promise<AuthResponse>
    logout(): Promise<void>
    getCurrentUser(): Promise<User>
    getAccessToken(): string | null
    setAccessToken(token: string): void
    setRefreshToken(token: string): void
    isAuthenticated(): boolean
    isTokenExpired(): boolean
}
```

#### 작업 11: AuthContext (상태 관리)
**File**: `MATHESIS-LAB_FRONT/contexts/AuthContext.tsx`

```typescript
# 요구사항:
- 사용자 상태 (user, isLoading, error)
- 로그인/로그아웃 기능
- 토큰 자동 갱신
- 토큰 저장/복구

# 제공:
interface AuthContextType {
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean
    error: string | null
    login: (email, password) => Promise<void>
    logout: () => Promise<void>
    register: (email, name, password) => Promise<void>
}
```

#### 작업 12: useAuth 훅
**File**: `MATHESIS-LAB_FRONT/hooks/useAuth.ts`

```typescript
# 사용:
const { user, login, logout, isAuthenticated } = useAuth()

# 기능:
- 자동 토큰 갱신
- 로그인 상태 유지
- 에러 처리
```

#### 작업 13: ProtectedRoute 컴포넌트
**File**: `MATHESIS-LAB_FRONT/components/ProtectedRoute.tsx`

```typescript
# 기능:
- 인증된 사용자만 접근
- 미인증 사용자 로그인 페이지로 리다이렉트
- 선택적 역할 기반 접근 제어

# 사용:
<ProtectedRoute path="/dashboard" component={Dashboard} requiredRole="user" />
```

#### 작업 14: 로그인 페이지
**File**: `MATHESIS-LAB_FRONT/pages/Login.tsx`

```typescript
# 요소:
- 이메일 입력
- 비밀번호 입력
- "로그인" 버튼
- "회원가입" 링크
- 에러 메시지
- 로딩 상태
- 비밀번호 찾기 링크 (선택)
```

#### 작업 15: 회원가입 페이지
**File**: `MATHESIS-LAB_FRONT/pages/Register.tsx`

```typescript
# 요소:
- 이메일 입력
- 이름 입력
- 비밀번호 입력
- 비밀번호 확인
- "회원가입" 버튼
- "로그인" 링크
- 비밀번호 강도 표시
- 유효성 검증
```

#### 작업 16: 프론트엔드 라우팅 업데이트
**File**: `MATHESIS-LAB_FRONT/App.tsx`

```typescript
# 변경사항:
- AuthProvider 래핑
- 로그인/회원가입 라우트 추가
- 기존 라우트를 ProtectedRoute로 감싸기
- OAuth 콜백 라우트 추가
```

#### 작업 17: 헤더 컴포넌트 업데이트
**File**: `MATHESIS-LAB_FRONT/components/Header.tsx`

```typescript
# 변경사항:
- 사용자 로그인 상태 표시
- 프로필 드롭다운 메뉴
- 로그아웃 버튼
```

#### 작업 18: 단위 테스트
**File**: `MATHESIS-LAB_FRONT/services/authService.test.ts`

```typescript
# 테스트 케이스:
- test_login_success
- test_login_failure
- test_register_success
- test_register_validation
- test_token_storage
- test_token_expiration
- (목표: 90% 커버리지)
```

#### 작업 19: E2E 테스트
**File**: `MATHESIS-LAB_FRONT/e2e/auth.spec.ts`

```typescript
# 테스트:
- test_complete_login_flow
- test_complete_register_flow
- test_protected_route_redirect
- test_logout_functionality
- test_session_persistence
```

### 1.3 데이터베이스 마이그레이션

#### 작업 20: 마이그레이션 파일 생성
**File**: `backend/app/db/migrations/002_add_users_and_sessions.py`

```sql
-- users 테이블 생성
CREATE TABLE users (
  user_id VARCHAR(36) PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255),
  profile_picture_url TEXT,
  role VARCHAR(50) DEFAULT 'user',
  is_active BOOLEAN DEFAULT true,
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP
);

-- user_sessions 테이블 생성 (선택)
CREATE TABLE user_sessions (
  session_id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  refresh_token_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,
  revoked_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 인덱스 생성
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
```

### 1.4 설정 파일 업데이트

#### 작업 21: 설정 업데이트
**File**: `backend/app/core/config.py`

```python
# 추가:
JWT_SECRET_KEY: str (from .env or Secret Manager)
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
BCRYPT_LOG_ROUNDS: int = 12
PASSWORD_MIN_LENGTH: int = 8
```

---

## Phase 2: GCP 연동 (7일)

### 2.1 GCP 프로젝트 설정

#### 작업 22: GCP 리소스 생성 (수동)
```
- GCP 프로젝트 생성
- Cloud SQL 인스턴스 생성 (PostgreSQL 15)
- Cloud Storage 버킷 생성
- Secret Manager 활성화
- Service Account 생성
- IAM 권한 설정
```

#### 작업 23: Secret Manager 설정
```
저장할 비밀:
- jwt-secret
- database-password
- gcp-service-account-key
- oauth-client-id (선택)
- oauth-client-secret (선택)
```

### 2.2 백엔드 GCP 통합

#### 작업 24: GCP Secret Manager 클라이언트
**File**: `backend/app/integrations/gcp_secrets.py`

```python
class GCPSecretsClient:
    async def get_secret(secret_id: str) -> str
    async def set_secret(secret_id: str, value: str)

# 사용:
jwt_secret = await secrets_client.get_secret('jwt-secret')
```

#### 작업 25: Cloud SQL 연결
**File**: `backend/app/db/cloudsql.py`

```python
# Cloud SQL Connector 사용
from google.cloud.sql.connector import Connector

class CloudSQLConnection:
    - 자동 연결 풀링
    - SSL 지원
    - 자동 재연결
```

#### 작업 26: Cloud Storage 클라이언트
**File**: `backend/app/integrations/gcp_storage.py`

```python
class GCPStorageClient:
    async def upload_file(bucket: str, path: str, data: bytes)
    async def download_file(bucket: str, path: str) -> bytes
    async def delete_file(bucket: str, path: str)
    async def list_files(bucket: str, prefix: str) -> List[str]
```

#### 작업 27: GCP 통합 테스트
**File**: `backend/tests/unit/test_gcp_integration.py`

```python
# 테스트:
- test_secret_retrieval (모크)
- test_cloud_storage_operations (모크)
- test_cloud_sql_connection (모크)
```

### 2.3 프론트엔드 GCP 연동

#### 작업 28: Google Sign-In 통합
**File**: `MATHESIS-LAB_FRONT/pages/Login.tsx`

```typescript
# 기능:
- Google Sign-In 버튼
- OAuth 콜백 처리
- 토큰 교환
- 자동 로그인

# 라이브러리:
@react-oauth/google
```

#### 작업 29: OAuth 콜백 핸들러
**File**: `MATHESIS-LAB_FRONT/pages/OAuthCallback.tsx`

```typescript
# 기능:
- Google에서 받은 토큰 처리
- 백엔드로 토큰 전송
- JWT 토큰 받기
- 사용자 정보 저장
- 리다이렉트
```

#### 작업 30: Backend OAuth 엔드포인트
**File**: `backend/app/api/v1/endpoints/auth.py`

```python
POST /api/v1/auth/google-callback
    - Google ID Token 검증
    - 사용자 생성 또는 조회
    - JWT 토큰 발급
```

---

## Phase 3: 컨테이너화 및 배포 (7일)

### 3.1 Docker 설정

#### 작업 31: Backend Dockerfile
**File**: `backend.Dockerfile`

```dockerfile
# 멀티 스테이지 빌드
- 빌드 스테이지: 의존성 설치
- 런타임 스테이지: 최소 크기
- 보안: root 제외, 읽기 전용 FS
```

#### 작업 32: Frontend Dockerfile
**File**: `MATHESIS-LAB_FRONT/Dockerfile`

```dockerfile
# 멀티 스테이지 빌드
- 빌드 스테이지: npm build
- 프로덕션 스테이지: Nginx
- 환경 변수 주입
```

#### 작업 33: Docker Compose
**File**: `docker-compose.yml`

```yaml
# 서비스:
- backend (FastAPI)
- frontend (Nginx)
- postgres (PostgreSQL)

# 네트워크: mathesis_network
# 볼륨: postgres_data

# 포트 매핑:
- 8000: backend
- 3000: frontend
- 5432: postgres
```

#### 작업 34: .dockerignore 파일
**Files**: `.dockerignore`, `MATHESIS-LAB_FRONT/.dockerignore`

```
# 제외:
- node_modules/
- .git/
- dist/
- __pycache__/
- .env
- .env.*.local
- *.db
- etc.
```

#### 작업 35: 로컬 테스트
```bash
docker-compose up
# http://localhost:3000 접속
# 로그인/회원가입 테스트
```

### 3.2 배포 자동화

#### 작업 36: GitHub Secrets 설정
```
필수 Secrets:
- GCP_PROJECT_ID
- GCP_SA_KEY (JSON)
- GCP_REGION
- CLOUD_SQL_CONNECTION_STRING
- JWT_SECRET
```

#### 작업 37: GitHub Actions 워크플로우
**File**: `.github/workflows/deploy.yml`

```yaml
# Jobs:
1. test-backend
2. test-frontend
3. build-and-push-backend
4. build-and-push-frontend
5. deploy-backend-cloud-run
6. deploy-frontend-cloud-run
7. run-migrations
8. post-deployment-tests
```

#### 작업 38: Cloud Run 배포 스크립트
**File**: `gcp/deploy-cloud-run.sh`

```bash
# 스크립트:
- Docker 이미지 빌드
- Container Registry에 푸시
- Cloud Run에 배포
- 환경 변수 설정
- 헬스 체크
```

---

## Phase 4: 모크업 배포 및 테스트 (5일)

### 4.1 스테이징 환경 배포

#### 작업 39: Staging 환경 설정
```
- staging.example.com (가상 도메인)
- 스테이징 데이터베이스
- 스테이징 Secret Manager
```

#### 작업 40: 모크업 테스트 계획
```
테스트 항목:
1. 사용자 인증 (전체 플로우)
2. CRUD 작업 (인증 후)
3. GCP 통합 (백업, 복원)
4. 성능 (응답 시간, 처리량)
5. 보안 (인증, 권한, SQL injection 등)
6. 신뢰성 (에러 처리, 복구)
```

### 4.2 테스트 스위트 작성

#### 작업 41: 통합 테스트 (E2E)
**File**: `tests/integration/e2e_deployment_test.py`

```python
# 테스트:
class TestDeploymentFlow:
    def test_user_registration_flow
    def test_user_login_flow
    def test_create_curriculum_authenticated
    def test_share_curriculum_with_user
    def test_gcp_backup_integration
    def test_gcp_restore_integration
    def test_api_rate_limiting
    def test_error_handling
```

#### 작업 42: 성능 테스트
**File**: `tests/performance/load_test.py`

```python
# 메트릭:
- 로그인 응답 시간 (< 500ms)
- API 처리량 (> 100 req/s)
- 데이터베이스 쿼리 시간 (< 100ms)
- 동시 사용자 (100+ users)
```

#### 작업 43: 보안 테스트
**File**: `tests/security/security_test.py`

```python
# 테스트:
- SQL injection 방지
- XSS 방지
- CSRF 방지
- 토큰 조작 감지
- 비인증 접근 차단
- 권한 검증
```

### 4.3 모크업 테스트 리포트

#### 작업 44: 테스트 리포트 생성
**File**: `tools/deployment_test_report_generator.py`

```python
# 생성 항목:
1. 테스트 요약
   - 전체 테스트 수
   - 통과/실패/건너뜀
   - 성공률

2. 환경별 결과
   - 로컬 docker-compose
   - 스테이징 Cloud Run
   - 통합 테스트

3. 성능 메트릭
   - 응답 시간
   - 처리량
   - 리소스 사용

4. 보안 검사 결과
   - 취약점 감지 여부
   - 정책 준수 여부

5. 배포 체크리스트
   - 완료/미완료 항목
   - 블로커 문제

6. 권장사항
```

---

## Phase 5: 최종 검증 및 운영 준비 (5일)

### 5.1 최종 테스트

#### 작업 45: 회귀 테스트
```bash
# 기존 기능 영향도 확인
pytest backend/tests/
npm test (MATHESIS-LAB_FRONT)
npx playwright test (E2E)
```

#### 작업 46: 성능 튜닝
```
- 데이터베이스 쿼리 최적화
- 캐싱 전략
- CDN 설정 (선택)
- 이미지 최적화
```

#### 작업 47: 문서화
```
생성 문서:
1. 배포 가이드
2. 운영 매뉴얼
3. 트러블슈팅 가이드
4. API 문서
5. 보안 가이드
6. 성능 튜닝 가이드
```

### 5.2 최종 배포 준비

#### 작업 48: 프로덕션 체크리스트
```
[ ] 모든 테스트 통과
[ ] 보안 검사 통과
[ ] 성능 기준 만족
[ ] 문서 완성
[ ] 백업 계획 수립
[ ] 모니터링 설정
[ ] 알림 규칙 설정
[ ] 재해 복구 계획 수립
[ ] 팀 교육 완료
```

#### 작업 49: 최종 테스트 리포트
```
생성 리포트:
- 모크업 배포 테스트 결과
- 모든 테스트 커버리지 > 85%
- 성능 벤치마크
- 보안 감사 결과
- 배포 준비 상태
```

---

## 📊 실행 추적

### 완료 기준

**Phase 1 완료**
- 모든 인증 테스트 통과
- 프론트엔드 로그인/회원가입 작동
- 데이터베이스 마이그레이션 성공

**Phase 2 완료**
- GCP 리소스 생성 완료
- Secret Manager 설정 완료
- OAuth 통합 작동

**Phase 3 완료**
- Docker 로컬 테스트 통과
- GitHub Actions 배포 성공
- 스테이징 환경 접근 가능

**Phase 4 완료**
- 모든 E2E 테스트 통과
- 성능 기준 달성
- 보안 검사 통과

**Phase 5 완료**
- 최종 테스트 리포트 생성
- 프로덕션 체크리스트 완료
- 문서화 완료

---

## 다음 단계

1. **계획 검토**: 아키텍처 팀 검토 및 승인
2. **도구 준비**: GCP 프로젝트, GitHub 설정
3. **팀 구성**: 각 역할별 담당자 지정
4. **상세 기술 스펙**: 각 작업별 상세 요구사항 수립
5. **구현 시작**: Phase 1부터 순차적 진행

---

**문서 생성**: 2025-11-16
**최종 검토**: 예정
