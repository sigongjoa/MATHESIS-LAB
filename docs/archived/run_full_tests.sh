#!/bin/bash

##############################################################################
# 통합 테스트 실행 스크립트
# E2E 테스트 → 자동 리포트 생성
##############################################################################

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

REPORT_TITLE="${1:-Full Test Report}"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

echo ""
echo "============================================================"
echo "🚀 시작: 통합 테스트 실행 및 리포트 생성"
echo "============================================================"
echo ""
echo "📋 Report Title: $REPORT_TITLE"
echo "⏰ Timestamp: $TIMESTAMP"
echo ""

# 1. 백엔드 서버 상태 확인
echo "1️⃣ 백엔드 서버 확인..."
if ! pgrep -f "uvicorn" > /dev/null; then
    echo "⚠️  백엔드 서버가 실행 중이 아닙니다."
    echo "   다른 터미널에서 실행: cd backend && python -m uvicorn app.main:app --reload"
    echo ""
fi

# 2. 프론트엔드 서버 상태 확인
echo "2️⃣프론트엔드 서버 확인..."
if ! pgrep -f "npm run dev" > /dev/null; then
    echo "⚠️  프론트엔드 서버가 실행 중이 아닙니다."
    echo "   다른 터미널에서 실행: cd MATHESIS-LAB_FRONT && npm run dev"
    echo ""
fi

# 3. E2E 테스트 실행
echo ""
echo "3️⃣ E2E 테스트 실행 중..."
echo "---"

cd "$PROJECT_ROOT/MATHESIS-LAB_FRONT"

# 스크린샷 디렉토리 정리 (선택사항)
# rm -rf e2e-screenshots
mkdir -p e2e-screenshots

# E2E 테스트 실행
if npx playwright test e2e/ --reporter=json --reporter=list 2>&1; then
    echo "---"
    echo "✅ E2E 테스트 완료"

    # 스크린샷 개수 확인
    SCREENSHOT_COUNT=$(ls -1 e2e-screenshots/*.png 2>/dev/null | wc -l)
    echo "📸 스크린샷: $SCREENSHOT_COUNT 개"

    if [ $SCREENSHOT_COUNT -gt 0 ]; then
        echo "   생성된 스크린샷:"
        ls -1 e2e-screenshots/*.png | sed 's|.*/||' | sed 's/^/     - /'
    fi
else
    echo "---"
    echo "⚠️  E2E 테스트 실행 중 경고 또는 실패"
    SCREENSHOT_COUNT=$(ls -1 e2e-screenshots/*.png 2>/dev/null | wc -l)
    echo "📸 수집된 스크린샷: $SCREENSHOT_COUNT 개"
fi

cd "$PROJECT_ROOT"

# 4. 테스트 리포트 생성
echo ""
echo "4️⃣ 테스트 리포트 생성 중..."
echo "---"

source .venv/bin/activate

python tools/test_report_generator.py --title "$REPORT_TITLE" 2>&1 | tail -20

echo "---"

# 5. 생성된 리포트 확인
echo ""
echo "5️⃣ 생성된 리포트 확인..."

REPORT_DIR="test_reports"
if [ -d "$REPORT_DIR" ]; then
    LATEST_MD=$(ls -t "$REPORT_DIR"/*.md 2>/dev/null | head -1)
    LATEST_PDF=$(ls -t "$REPORT_DIR"/*.pdf 2>/dev/null | head -1)

    if [ -n "$LATEST_MD" ]; then
        MD_SIZE=$(du -h "$LATEST_MD" | cut -f1)
        echo "✅ Markdown: $LATEST_MD ($MD_SIZE)"
    fi

    if [ -n "$LATEST_PDF" ]; then
        PDF_SIZE=$(du -h "$LATEST_PDF" | cut -f1)
        echo "✅ PDF: $LATEST_PDF ($PDF_SIZE)"
    fi
fi

echo ""
echo "============================================================"
echo "✅ 완료: 테스트 실행 및 리포트 생성 완료"
echo "============================================================"
echo ""
echo "📁 리포트 위치: $PROJECT_ROOT/test_reports/"
echo ""
echo "다음 단계:"
echo "  - MD 리포트 확인: cat test_reports/$LATEST_MD | head -50"
echo "  - PDF 리포트 확인: open test_reports/$LATEST_PDF"
echo ""
