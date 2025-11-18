# GitHub Pages 자동 배포 설정 가이드

## 개요

이 프로젝트는 CI/CD 파이프라인에서 자동으로 생성된 테스트 리포트를 GitHub Pages에 배포합니다.

**배포 URL:** `https://sigongjoa.github.io/MATHESIS-LAB/`

## 자동 배포 구조

```
GitHub Actions Workflow (test-and-report.yml)
    ↓
1. 백엔드 테스트 실행 (pytest)
2. 프론트엔드 테스트 실행 (npm test)
3. E2E 테스트 실행 (Playwright)
    ↓
4. 테스트 리포트 생성 (test_report_generator.py)
5. GitHub Pages 인덱스 생성 (generate_pages_index.py)
    ↓
6. peaceiris/actions-gh-pages로 gh-pages 브랜치에 배포
    ↓
7. GitHub Pages에서 자동으로 호스팅
```

## 배포 대상

각 CI/CD 실행 후 테스트 리포트가 다음 위치에 배포됩니다:

```
https://sigongjoa.github.io/MATHESIS-LAB/
├── index.html                          # 메인 페이지 (모든 리포트 목록)
└── reports/
    ├── {run_number_1}/
    │   ├── README.md                   # 마크다운 리포트
    │   ├── README.pdf                  # PDF 리포트
    │   └── screenshots/                # E2E 테스트 스크린샷
    ├── {run_number_2}/
    └── {run_number_N}/
```

## 필수 설정

### 1. GitHub Pages 활성화

GitHub 리포지토리 설정 → Pages 섹션에서:

1. **Source 선택:** Deploy from a branch
2. **Branch 선택:** `gh-pages`
3. **Folder 선택:** `/ (root)`

```
리포지토리 설정 경로:
Settings → Pages → Build and deployment
  Source: Deploy from a branch
  Branch: gh-pages / (root)
```

### 2. 워크플로우 권한

GitHub 리포지토리 설정 → Actions → General:

1. **Workflow permissions:** Read and write permissions
2. **Allow GitHub Actions to create and approve pull requests:** 체크

```
리포지토리 설정 경로:
Settings → Actions → General → Workflow permissions
  ☑ Read and write permissions
```

## 파일 설명

### 1. `.github/workflows/test-and-report.yml`

GitHub Actions 워크플로우 정의:
- 모든 테스트 (백엔드, 프론트엔드, E2E) 실행
- `test_report_generator.py` 실행으로 리포트 생성
- `generate_pages_index.py` 실행으로 인덱스 생성
- `peaceiris/actions-gh-pages`로 gh-pages 브랜치에 배포

**주요 단계:**
```yaml
- name: Deploy test report to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./test_reports
    destination_dir: reports/${{ github.run_number }}
    keep_files: true
```

### 2. `tools/generate_pages_index.py`

GitHub Pages 메인 페이지 생성:
- `test_reports/` 디렉토리의 모든 리포트 스캔
- 아름다운 HTML 인덱스 페이지 생성
- 최근 20개 리포트 표시
- 각 리포트별 MD/PDF/스크린샷 링크 제공

**생성 파일:**
- `test_reports/index.html` - GitHub Pages 메인 페이지

### 3. `tools/test_report_generator.py`

이미 존재하는 리포트 생성 도구:
- 백엔드 테스트 결과 파싱
- 프론트엔드 테스트 결과 파싱
- E2E 테스트 결과 및 스크린샷 수집
- README.md (마크다운 리포트) 생성
- README.pdf (PDF 리포트) 생성

**생성 결과:**
```
test_reports/
└── {report_title}__{timestamp}/
    ├── README.md
    ├── README.pdf
    └── screenshots/
        ├── screenshot_1.png
        ├── screenshot_2.png
        └── ...
```

## 배포 플로우

### 자동 배포 (CI/CD)

1. **push to master/main/develop** → GitHub Actions 트리거
2. 모든 테스트 실행
3. 테스트 리포트 생성
4. GitHub Pages 인덱스 생성
5. `peaceiris/actions-gh-pages` 액션으로 배포
6. 자동으로 GitHub Pages 갱신

### 수동 배포

GitHub Actions의 "Test & Report Generation" 워크플로우에서:
- "Run workflow" → "Run workflow" 클릭
- 수동으로 테스트 및 배포 실행 가능

## PR에서 테스트 리포트 확인

PR이 생성되면, GitHub Actions이 자동으로 다음 두 링크를 댓글로 추가:

```markdown
📊 Test Report Generated

## Summary
[테스트 결과 요약]

[View full report on GitHub Pages](https://sigongjoa.github.io/MATHESIS-LAB/reports/{run_number}/)

[View in CI/CD artifacts](https://github.com/sigongjoa/MATHESIS-LAB/actions/runs/{run_id})
```

## 테스트 리포트 URL 구조

### 메인 페이지
```
https://sigongjoa.github.io/MATHESIS-LAB/
```

### 특정 CI/CD 실행 리포트
```
https://sigongjoa.github.io/MATHESIS-LAB/reports/{run_number}/
```

예시:
```
https://sigongjoa.github.io/MATHESIS-LAB/reports/12345/README.md
https://sigongjoa.github.io/MATHESIS-LAB/reports/12345/README.pdf
https://sigongjoa.github.io/MATHESIS-LAB/reports/12345/screenshots/
```

## 주요 특징

### ✅ 자동 생성
- 모든 push 시 자동으로 테스트 리포트 생성
- 매번 수동으로 생성할 필요 없음

### ✅ 버전 관리
- 각 CI/CD 실행별로 독립적인 디렉토리 생성
- `run_number`로 자동 구분 (예: `reports/12345/`)
- 과거 모든 리포트 보존

### ✅ 웹 접근
- 누구나 브라우저에서 바로 확인 가능
- 공개 저장소이면 로그인 필요 없음
- 모바일에서도 지원

### ✅ 시각화
- 아름다운 인덱스 페이지
- 테스트 결과 통계
- 스크린샷 갤러리
- PDF 및 마크다운 형식

### ✅ 이력 관리
- `keep_files: true`로 과거 리포트 유지
- 최대 20개 최신 리포트만 목록에 표시
- 전체 히스토리는 GitHub 저장소에 보존

## 트러블슈팅

### GitHub Pages가 배포되지 않음

1. **Settings → Pages** 확인:
   - Branch: `gh-pages` 선택됨?
   - Folder: `/ (root)` 선택됨?

2. **Actions 권한** 확인:
   - Settings → Actions → General
   - "Read and write permissions" 활성화?

3. **워크플로우 실행 확인**:
   - Actions 탭에서 "Test & Report Generation" 완료됨?
   - 모든 단계가 성공(초록색)인가?

### 배포되었는데 페이지가 보이지 않음

1. GitHub Pages 배포 대기:
   - 배포는 최대 1분 걸릴 수 있음

2. 캐시 삭제:
   - Ctrl+Shift+R (Windows/Linux)
   - Cmd+Shift+R (Mac)

3. 직접 URL 확인:
   ```bash
   https://sigongjoa.github.io/MATHESIS-LAB/
   ```

### gh-pages 브랜치가 보이지 않음

1. 첫 배포 후 자동 생성됨
2. `Settings → Pages`에서 `gh-pages` 보이는지 확인
3. 없으면 첫 배포 완료될 때까지 기다림

## 참고 자료

- GitHub Pages 공식 문서: https://pages.github.com/
- peaceiris/actions-gh-pages: https://github.com/peaceiris/actions-gh-pages
- GitHub Actions 문서: https://docs.github.com/en/actions

## 다음 단계

현재 구현:
- ✅ 테스트 리포트 자동 생성
- ✅ GitHub Pages 자동 배포
- ✅ 인덱스 페이지 생성

향후 개선 계획:
- [ ] 테스트 결과 통계 대시보드
- [ ] 과거 리포트 비교 기능
- [ ] Slack/Discord 알림 연동
- [ ] 테스트 커버리지 추적
- [ ] 성능 벤치마크 그래프

---

**마지막 업데이트:** 2025-11-18
