# ⚙️ GitHub Pages 설정 체크리스트

GitHub Pages에서 테스트 리포트를 자동으로 배포하려면 다음 설정이 필요합니다.

**소요 시간:** 약 5분

## ✅ 체크리스트

### 1️⃣ GitHub Pages 활성화

```
리포지토리: https://github.com/sigongjoa/MATHESIS-LAB

1. Settings 탭 클릭
   https://github.com/sigongjoa/MATHESIS-LAB/settings

2. 왼쪽 메뉴에서 "Pages" 선택

3. Build and deployment 섹션:

   Source 선택:
   ☑ Deploy from a branch

   Branch 선택:
   ☑ gh-pages / (root)

4. 저장 (Save)
```

### 2️⃣ GitHub Actions 권한 설정

```
리포지토리: https://github.com/sigongjoa/MATHESIS-LAB

1. Settings 탭 클릭

2. 왼쪽 메뉴에서 "Actions" > "General" 선택
   https://github.com/sigongjoa/MATHESIS-LAB/settings/actions/general

3. Workflow permissions 섹션:

   ☑ Read and write permissions

4. Allow GitHub Actions to create and approve pull requests:
   ☑ 체크

5. 저장 (Save)
```

### 3️⃣ 워크플로우 실행 (첫 배포)

이 설정은 이미 코드에 포함되어 있습니다:

```yaml
# .github/workflows/test-and-report.yml

- name: Deploy test report to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./test_reports
    destination_dir: reports/${{ github.run_number }}
    keep_files: true
```

첫 배포 트리거:

```bash
git push origin master
```

## 📊 확인 방법

### 1. GitHub Pages 활성화 확인

```
https://github.com/sigongjoa/MATHESIS-LAB/settings/pages
```

다음이 표시되어야 함:

```
✅ Your site is published at https://sigongjoa.github.io/MATHESIS-LAB/
```

### 2. gh-pages 브랜치 확인

```
https://github.com/sigongjoa/MATHESIS-LAB/branches
```

`gh-pages` 브랜치가 보여야 함 (첫 배포 후 자동 생성)

### 3. GitHub Actions 실행 확인

```
https://github.com/sigongjoa/MATHESIS-LAB/actions
```

1. "Test & Report Generation" 워크플로우 선택
2. 최근 실행 선택
3. "Deploy test report to GitHub Pages" 단계 확인
4. ✅ 초록색 체크 표시 = 성공

### 4. 웹사이트 접속 확인

```
https://sigongjoa.github.io/MATHESIS-LAB/
```

다음이 표시되어야 함:

```
📊 MATHESIS LAB Test Reports
CI/CD 파이프라인에서 자동 생성된 테스트 결과

[통계 대시보드]
[최근 리포트 목록]
```

## 🔄 자동 배포 테스트

### 방법 1: 자동 배포 (권장)

다음 명령어로 테스트 배포 트리거:

```bash
cd /mnt/d/progress/MATHESIS\ LAB

# 작은 파일 변경 후 push
echo "# Test deployment" >> README.md
git add README.md
git commit -m "test: trigger GitHub Pages deployment"
git push origin master
```

### 방법 2: 수동 배포

```
https://github.com/sigongjoa/MATHESIS-LAB/actions

1. "Test & Report Generation" 워크플로우 선택
2. "Run workflow" 드롭다운 클릭
3. "Run workflow" 버튼 클릭
4. 완료 대기
```

## 📈 배포 후 확인

배포 완료 후 (약 1-2분):

```
https://sigongjoa.github.io/MATHESIS-LAB/
```

다음 요소가 보여야 함:

✅ 메인 페이지 (index.html)
✅ 통계 대시보드 (총 리포트 수, 성공률 등)
✅ 최신 리포트 카드 (README.md, README.pdf, Screenshots 링크)

## 🆘 트러블슈팅

### Q: GitHub Pages 활성화 되었는데 배포가 안 됨

**A:** 다음을 확인하세요:

1. GitHub Actions 실행 확인:
   ```
   https://github.com/sigongjoa/MATHESIS-LAB/actions
   ```
   - 모든 단계가 ✅ (초록색)인가?
   - "Deploy test report to GitHub Pages" 단계 실패한 건 아닌가?

2. Actions 권한 확인:
   ```
   Settings → Actions → General
   ```
   - "Read and write permissions" 활성화?
   - "Allow GitHub Actions to create and approve pull requests" 체크?

3. gh-pages 브랜치 확인:
   ```
   https://github.com/sigongjoa/MATHESIS-LAB/branches
   ```
   - gh-pages 브랜치 존재?
   - Pages 설정에서 gh-pages 브랜치 선택?

### Q: 페이지가 보이지 않음 (404 error)

**A:** 다음을 시도하세요:

1. **캐시 삭제:**
   - Windows/Linux: Ctrl+Shift+R
   - Mac: Cmd+Shift+R

2. **잠시 대기:**
   - GitHub Pages 배포는 최대 1분 소요 가능
   - 2-3분 후 다시 접속

3. **GitHub 상태 확인:**
   ```
   https://www.githubstatus.com/
   ```
   - GitHub Pages 정상 작동 중?

### Q: Actions 권한을 수정했는데도 작동 안 함

**A:** 다음을 시도하세요:

1. 워크플로우 파일 확인:
   ```
   .github/workflows/test-and-report.yml
   ```
   - 파일 존재?
   - 파일 내용 정상?

2. 새로운 push로 워크플로우 재실행:
   ```bash
   git commit --allow-empty -m "trigger workflow"
   git push origin master
   ```

3. GitHub Actions 로그 상세 확인:
   ```
   https://github.com/sigongjoa/MATHESIS-LAB/actions
   ```
   - 각 단계별 에러 메시지 확인
   - "Deploy test report to GitHub Pages" 단계의 에러 확인

## 📚 참고 자료

- [GitHub Pages 공식 문서](https://pages.github.com/)
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages)

## ✨ 완료 확인

다음이 모두 ✅일 때 설정 완료:

- [ ] GitHub Pages 활성화됨 (Settings → Pages)
- [ ] gh-pages 브랜치 존재
- [ ] Actions 권한 "Read and write" 설정됨
- [ ] GitHub Actions 실행 완료 (✅ 초록색)
- [ ] 메인 페이지 접속 가능
  ```
  https://sigongjoa.github.io/MATHESIS-LAB/
  ```
- [ ] 최신 리포트 표시됨

---

**다음 단계:** [GitHub Pages 배포 가이드](./GITHUB_PAGES_DEPLOYMENT_GUIDE.md)
