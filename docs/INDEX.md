# MATHESIS LAB 문서 인덱스

이 문서는 MATHESIS LAB 프로젝트의 모든 문서를 분류하고 설명합니다.

## 📚 폴더 구조

```
docs/
├── 📋 Core Documentation (최상위)
│   ├── README.md - 문서 가이드
│   ├── sdd_*.md - 소프트웨어 설계 문서 (SDD)
│   ├── tdd_*.md - 테스트 주도 개발 문서 (TDD)
│   └── student_learning_objectives.md - 학습 목표
│
├── 🏗️ planning/ - 기획 및 구현 계획
│   ├── IMPLEMENTATION_PLAN.md - 전체 구현 계획
│   ├── IMPLEMENTATION_REPORT.md - 구현 보고서
│   ├── IMPLEMENTATION_SUMMARY.md - 구현 요약
│   ├── PENDING_FEATURES.md - 대기 중인 기능
│   ├── MIGRATION_GUIDE.md - 마이그레이션 가이드
│   ├── ARCHITECTURE_INTEGRATION_REVISED.md - 아키텍처 통합 (수정판)
│   └── DEPLOYMENT_ARCHITECTURE_PLAN.md - 배포 아키텍처 계획
│
├── 🔧 troubleshooting/ - 문제 해결 및 수정 기록 (최상위)
│   ├── TROUBLESHOOTING.md - Phase 2 전체 문제 해결 및 수정 기록 📌 NEW
│   ├── CI_CD_FIX_SUMMARY.md - CI/CD 수정 요약
│   ├── COMPLETION_SUMMARY.md - 완료 요약
│   ├── DEPLOYMENT_SUMMARY.md - 배포 요약
│   ├── GITHUB_ACTIONS_FIX_SUMMARY.md - GitHub Actions 수정 요약
│   └── SESSION_JOURNEY.md - 세션 진행 기록
│
├── 📖 reference/ - 참고 자료 및 가이드
│   ├── ENVIRONMENT_SETUP.md - 환경 설정 가이드
│   ├── GOOGLE_OAUTH2_*.md - Google OAuth2 설정 가이드
│   ├── OAUTH2_*.md - OAuth2 구현 가이드
│   ├── GEMINI.md - Gemini AI 설정
│   ├── METADATA_GENERATION_GUIDE.md - 메타데이터 생성 가이드
│   ├── REPORT_GENERATION_PIPELINE.md - 보고서 생성 파이프라인
│   └── TEST_REPORT_GENERATOR_SUMMARY.md - 테스트 보고서 생성기
│
├── 🧪 testing/ - 테스트 관련 문서
│   ├── E2E_TESTING_NEXT_STEPS.md - E2E 테스트 다음 단계
│   ├── E2E_TESTS_GUIDE.md - E2E 테스트 가이드
│   ├── E2E_TEST_STRUCTURE.md - E2E 테스트 구조
│   ├── FRONTEND_TESTING_GUIDE.md - 프론트엔드 테스트 가이드
│   └── frontend_testing_strategy.md - 프론트엔드 테스트 전략
│
├── 🌐 gcp/ - Google Cloud Platform 통합
│   ├── README.md
│   ├── SDD_GCP_INTEGRATION.md
│   └── SDD_GCP_INTEGRATION_REVISED.md
│
├── 📦 node/ - 노드 관리 시스템
│   ├── README.md
│   ├── SDD_NODE_MANAGEMENT.md
│   └── SDD_NODE_MANAGEMENT_REVISED.md
│
└── 📦 archived/ - 오래된 및 참고용 파일
    ├── .pytest_output.log - pytest 실행 로그
    ├── .pytest_output_fresh.log - 신규 pytest 실행 로그
    ├── .vitest_output.log - vitest 실행 로그
    ├── pytest_failures.log - pytest 실패 로그
    ├── test.config.json - 테스트 설정
    ├── run_complete_test_suite.py - 구 테스트 스크립트
    ├── run_e2e_and_report.sh - 구 E2E 테스트 스크립트
    ├── run_full_tests.sh - 구 전체 테스트 스크립트
    └── run_tests_and_report.py - 구 테스트 보고서 스크립트
```

## 🎯 빠른 참조

### 새로 시작하는 개발자
1. **sdd_software_requirements.md** - 요구사항 이해
2. **sdd_software_architecture.md** - 아키텍처 이해
3. **ENVIRONMENT_SETUP.md** - 환경 설정
4. **IMPLEMENTATION_PLAN.md** (planning) - 구현 계획

### 기능 구현
1. **planning/IMPLEMENTATION_PLAN.md** - 전체 구현 계획
2. **sdd_api_specification.md** - API 명세
3. **sdd_database_design.md** - 데이터베이스 설계
4. **planning/ARCHITECTURE_INTEGRATION_REVISED.md** - 아키텍처 통합

### OAuth2 구현
1. **reference/GOOGLE_OAUTH2_CREDENTIALS_GUIDE.md** - 자격증명 생성
2. **reference/OAUTH2_IMPLEMENTATION_COMPLETE.md** - 구현 가이드
3. **reference/OAUTH2_QUICK_START.md** - 빠른 시작

### 테스트
1. **testing/E2E_TEST_STRUCTURE.md** - E2E 테스트 구조
2. **testing/FRONTEND_TESTING_GUIDE.md** - 프론트엔드 테스트
3. **tdd_test_cases.md** - 테스트 케이스

### 배포
1. **planning/DEPLOYMENT_ARCHITECTURE_PLAN.md** - 배포 아키텍처
2. **troubleshooting/DEPLOYMENT_SUMMARY.md** - 배포 기록
3. **reference/REPORT_GENERATION_PIPELINE.md** - 보고서 생성

## 📝 문서 분류 정보

| 카테고리 | 목적 | 주요 파일 |
|---------|------|---------|
| **planning/** | 기획, 설계, 계획 | IMPLEMENTATION_PLAN.md, ARCHITECTURE_INTEGRATION_REVISED.md |
| **troubleshooting/** | 문제 해결, 수정 기록 | CI_CD_FIX_SUMMARY.md, DEPLOYMENT_SUMMARY.md |
| **reference/** | 가이드, 설정, 참고자료 | ENVIRONMENT_SETUP.md, OAUTH2_*.md |
| **testing/** | 테스트 관련 문서 | E2E_TEST_STRUCTURE.md, FRONTEND_TESTING_GUIDE.md |
| **gcp/** | GCP 통합 관련 | SDD_GCP_INTEGRATION.md |
| **node/** | 노드 관리 관련 | SDD_NODE_MANAGEMENT.md |
| **archived/** | 오래된 파일, 로그 | 레거시 스크립트, 실행 로그 |

## 🔍 문서 찾기 가이드

- **"새로운 기능을 구현하려면?"** → `planning/` 폴더 확인
- **"에러가 발생했어, 어떻게 해?"** → `troubleshooting/` 폴더 확인
- **"OAuth2를 설정하려면?"** → `reference/` 폴더에서 OAUTH2로 시작하는 파일 확인
- **"E2E 테스트는?"** → `testing/` 폴더 확인
- **"아키텍처는?"** → `sdd_software_architecture.md` 또는 `planning/ARCHITECTURE_INTEGRATION_REVISED.md` 확인
- **"과거 로그/기록?"** → `archived/` 폴더 확인

## 🚀 주요 리소스

- **프로젝트 설정**: ENVIRONMENT_SETUP.md
- **API 스펙**: sdd_api_specification.md, api_specification.md
- **데이터베이스**: sdd_database_design.md
- **OAuth2**: reference/OAUTH2_IMPLEMENTATION_COMPLETE.md
- **E2E 테스트**: testing/E2E_TEST_STRUCTURE.md
- **배포**: planning/DEPLOYMENT_ARCHITECTURE_PLAN.md

---

**마지막 업데이트**: 2025-11-17
**작성자**: Claude Code (문서 정리 및 분류)
