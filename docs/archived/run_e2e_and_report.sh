#!/bin/bash
# 완전 자동화된 테스트 + 리포트 생성 스크립트
# Frontend 서버 자동 시작 → E2E 테스트 → 리포트 생성

set -e

PROJECT_ROOT="/mnt/d/progress/MATHESIS LAB"
FRONTEND_DIR="$PROJECT_ROOT/MATHESIS-LAB_FRONT"
BACKEND_DIR="$PROJECT_ROOT"
FRONTEND_PORT=3002
BACKEND_PORT=8000

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# 1. 서버 상태 확인 함수
check_server() {
    local port=$1
    local name=$2

    nc -z localhost $port > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "$name 서버 실행 중 (포트 $port)"
        return 0
    else
        print_info "$name 서버 대기 중..."
        return 1
    fi
}

# 2. 백엔드 서버 시작
start_backend() {
    print_header "백엔드 서버 시작"

    if check_server $BACKEND_PORT "Backend"; then
        return 0
    fi

    cd "$BACKEND_DIR"
    source .venv/bin/activate

    print_info "FastAPI 서버 시작 중..."
    nohup python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/backend.pid

    print_info "백엔드 서버 시작 (PID: $BACKEND_PID), 초기화 대기 중..."
    sleep 3

    # 서버가 시작될 때까지 대기 (최대 30초)
    for i in {1..30}; do
        if check_server $BACKEND_PORT "Backend"; then
            print_success "백엔드 서버 준비 완료"
            return 0
        fi
        sleep 1
    done

    print_error "백엔드 서버 시작 실패"
    cat /tmp/backend.log
    exit 1
}

# 3. 프론트엔드 서버 시작
start_frontend() {
    print_header "프론트엔드 서버 시작"

    if check_server $FRONTEND_PORT "Frontend"; then
        return 0
    fi

    cd "$FRONTEND_DIR"

    print_info "npm run dev 시작 중..."
    nohup npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/frontend.pid

    print_info "프론트엔드 서버 시작 (PID: $FRONTEND_PID), 초기화 대기 중..."
    sleep 5

    # 서버가 시작될 때까지 대기 (최대 30초)
    for i in {1..30}; do
        if check_server $FRONTEND_PORT "Frontend"; then
            print_success "프론트엔드 서버 준비 완료"
            return 0
        fi
        sleep 1
    done

    print_error "프론트엔드 서버 시작 실패"
    cat /tmp/frontend.log
    exit 1
}

# 4. E2E 테스트 실행
run_e2e_tests() {
    print_header "E2E 테스트 실행"

    cd "$FRONTEND_DIR"

    # e2e-screenshots 디렉토리 생성
    mkdir -p e2e-screenshots

    print_info "GCP 기능 E2E 테스트 실행 중..."

    if npx playwright test e2e/gcp-features.spec.ts --reporter=list; then
        print_success "E2E 테스트 완료"
        return 0
    else
        print_error "E2E 테스트 중 오류 발생"
        return 1
    fi
}

# 5. 테스트 리포트 생성
generate_report() {
    print_header "테스트 리포트 생성"

    cd "$BACKEND_DIR"
    source .venv/bin/activate

    TITLE="${1:-GCP UI/UX Implementation Test Report}"

    print_info "리포트 생성 중 (제목: $TITLE)..."

    if python tools/test_report_generator.py --title "$TITLE"; then
        print_success "테스트 리포트 생성 완료"

        # 최신 리포트 파일 찾기
        LATEST_MD=$(ls -t "$BACKEND_DIR/test_reports"/*.md 2>/dev/null | head -1)
        if [ -n "$LATEST_MD" ]; then
            print_success "리포트 경로: $LATEST_MD"

            # PDF도 있으면 표시
            LATEST_PDF="${LATEST_MD%.md}.pdf"
            if [ -f "$LATEST_PDF" ]; then
                print_success "PDF 리포트: $LATEST_PDF"
            fi
        fi

        return 0
    else
        print_error "리포트 생성 실패"
        return 1
    fi
}

# 6. 서버 종료
cleanup() {
    print_header "서버 종료"

    if [ -f /tmp/backend.pid ]; then
        BACKEND_PID=$(cat /tmp/backend.pid)
        if kill $BACKEND_PID 2>/dev/null; then
            print_success "백엔드 서버 종료 (PID: $BACKEND_PID)"
        fi
        rm -f /tmp/backend.pid
    fi

    if [ -f /tmp/frontend.pid ]; then
        FRONTEND_PID=$(cat /tmp/frontend.pid)
        if kill $FRONTEND_PID 2>/dev/null; then
            print_success "프론트엔드 서버 종료 (PID: $FRONTEND_PID)"
        fi
        rm -f /tmp/frontend.pid
    fi

    # 자식 프로세스도 모두 종료
    killall npm 2>/dev/null || true
    killall node 2>/dev/null || true

    print_success "모든 서버 종료 완료"
}

# 메인 실행 흐름
main() {
    print_header "🚀 완전 자동화 테스트 + 리포트 생성"

    # Ctrl+C 처리
    trap cleanup EXIT INT TERM

    # 1. 백엔드 시작
    start_backend

    # 2. 프론트엔드 시작
    start_frontend

    # 3. E2E 테스트 실행
    run_e2e_tests

    # 4. 리포트 생성
    REPORT_TITLE="${1:-GCP UI/UX Implementation - Complete Test Report}"
    generate_report "$REPORT_TITLE"

    print_header "✅ 모든 작업 완료!"
}

# 스크립트 실행
main "$@"
