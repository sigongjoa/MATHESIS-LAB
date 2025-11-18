#!/usr/bin/env python3
"""
완전 자동화된 E2E 테스트 + 리포트 생성 스크립트
- 백엔드 서버 자동 시작
- 프론트엔드 서버 자동 시작
- E2E 테스트 실행
- 테스트 리포트 생성
- 모든 서버 자동 종료
"""

import os
import sys
import subprocess
import time
import socket
import signal
import atexit
import json
from pathlib import Path
from typing import Optional, Dict, Any

# 설정 파일 로드
CONFIG_FILE = Path("/mnt/d/progress/MATHESIS LAB/test.config.json")
with open(CONFIG_FILE, 'r') as f:
    CONFIG = json.load(f)

# 경로 설정
PROJECT_ROOT = Path(CONFIG['paths']['project_root'])
FRONTEND_DIR = PROJECT_ROOT / CONFIG['paths']['frontend_dir']
BACKEND_DIR = PROJECT_ROOT / CONFIG['paths']['backend_dir']

# 포트 설정
BACKEND_PORT = CONFIG['backend']['port']
BACKEND_HOST = CONFIG['backend']['host']
BACKEND_STARTUP_TIMEOUT = CONFIG['backend']['startup_timeout']
BACKEND_STARTUP_MESSAGES = CONFIG['backend']['startup_messages']

FRONTEND_PORT = CONFIG['frontend']['port']
FRONTEND_HOST = CONFIG['frontend']['host']
FRONTEND_STARTUP_TIMEOUT = CONFIG['frontend']['startup_timeout']
FRONTEND_STARTUP_MESSAGES = CONFIG['frontend']['startup_messages']

# 색상 정의
class Color:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RESET = '\033[0m'

# 프로세스 저장
processes = {
    'backend': None,
    'frontend': None,
}

def print_header(text: str):
    """헤더 출력"""
    print(f"\n{Color.BLUE}{'='*50}")
    print(f"{text}")
    print(f"{'='*50}{Color.RESET}\n")

def print_success(text: str):
    """성공 메시지 출력"""
    print(f"{Color.GREEN}✅ {text}{Color.RESET}")

def print_error(text: str):
    """오류 메시지 출력"""
    print(f"{Color.RED}❌ {text}{Color.RESET}")

def print_info(text: str):
    """정보 메시지 출력"""
    print(f"{Color.YELLOW}ℹ️  {text}{Color.RESET}")

def check_port_available(port: int) -> bool:
    """포트가 사용 중인지 확인"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def wait_for_port(port: int, timeout: int = 30) -> bool:
    """포트가 준비될 때까지 대기"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_port_available(port):
            return True
        time.sleep(1)
    return False

def start_backend() -> bool:
    """백엔드 서버 시작"""
    print_header("백엔드 서버 시작")

    if check_port_available(BACKEND_PORT):
        print_success(f"백엔드 서버 이미 실행 중 (포트 {BACKEND_PORT})")
        return True

    print_info("FastAPI 서버 시작 중...")

    # 가상환경 활성화하고 서버 시작
    cmd = f'bash -c "cd \\"{BACKEND_DIR}\\" && source .venv/bin/activate && python -m uvicorn backend.app.main:app --reload --host {BACKEND_HOST} --port {BACKEND_PORT}"'

    print_info(f"실행 명령어: {cmd}")

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # stderr를 stdout으로 병합
        preexec_fn=os.setsid,  # 프로세스 그룹 생성
        text=True,
        bufsize=1  # 라인 버퍼링
    )

    processes['backend'] = process
    print_info(f"백엔드 서버 시작됨 (PID: {process.pid})")
    print_info("서버 출력 로그:")
    print_info("=" * 50)

    # 실시간으로 로그 출력
    start_time = time.time()
    timeout = BACKEND_STARTUP_TIMEOUT

    while time.time() - start_time < timeout:
        line = process.stdout.readline()
        if line:
            print(f"  {line.rstrip()}")
            # 설정된 시작 완료 메시지 확인
            if any(msg in line for msg in BACKEND_STARTUP_MESSAGES):
                print_info("=" * 50)
                print_success("백엔드 서버 준비 완료")
                return True

        # 포트 체크
        if check_port_available(BACKEND_PORT):
            print_info("=" * 50)
            print_success("백엔드 서버 준비 완료 (포트 감지)")
            return True

        time.sleep(0.5)

    print_info("=" * 50)
    print_error("백엔드 서버 시작 실패 (타임아웃)")

    return False

def start_frontend() -> bool:
    """프론트엔드 서버 시작"""
    print_header("프론트엔드 서버 시작")

    if check_port_available(FRONTEND_PORT):
        print_success(f"프론트엔드 서버 이미 실행 중 (포트 {FRONTEND_PORT})")
        return True

    print_info("npm run dev 시작 중...")

    cmd = f'bash -c "cd \\"{FRONTEND_DIR}\\" && npm run dev -- --host {FRONTEND_HOST} --port {FRONTEND_PORT}"'

    print_info(f"실행 명령어: {cmd}")

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # stderr를 stdout으로 병합
        preexec_fn=os.setsid,  # 프로세스 그룹 생성
        text=True,
        bufsize=1  # 라인 버퍼링
    )

    processes['frontend'] = process
    print_info(f"프론트엔드 서버 시작됨 (PID: {process.pid})")
    print_info("서버 출력 로그:")
    print_info("=" * 50)

    # 실시간으로 로그 출력
    start_time = time.time()
    timeout = FRONTEND_STARTUP_TIMEOUT

    while time.time() - start_time < timeout:
        line = process.stdout.readline()
        if line:
            print(f"  {line.rstrip()}")
            # 설정된 시작 완료 메시지 확인
            if any(msg in line for msg in FRONTEND_STARTUP_MESSAGES):
                print_info("=" * 50)
                print_success("프론트엔드 서버 준비 완료")
                return True

        # 포트 체크
        if check_port_available(FRONTEND_PORT):
            print_info("=" * 50)
            print_success("프론트엔드 서버 준비 완료 (포트 감지)")
            return True

        time.sleep(0.5)

    print_info("=" * 50)
    print_error("프론트엔드 서버 시작 실패 (타임아웃)")

    return False

def run_e2e_tests() -> bool:
    """E2E 테스트 실행"""
    print_header("E2E 테스트 실행")

    # e2e-screenshots 디렉토리 생성
    screenshots_dir = FRONTEND_DIR / "e2e-screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    print_info("GCP 기능 E2E 테스트 실행 중...")

    cmd = f'bash -c "cd \\"{FRONTEND_DIR}\\" && npx playwright test e2e/gcp-features.spec.ts --reporter=list"'

    print_info(f"실행 명령어: {cmd}")
    print_info("=" * 50)

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print_info("테스트 출력 로그:")
    print_info("=" * 50)

    # 실시간 로그 출력
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(f"  {line.rstrip()}")

    process.wait()
    print_info("=" * 50)

    if process.returncode == 0:
        print_success("E2E 테스트 완료")
        return True
    else:
        print_error(f"E2E 테스트 실패 (종료 코드: {process.returncode})")
        return False

def generate_report(title: str = "GCP UI/UX Implementation - Complete Test Report") -> bool:
    """테스트 리포트 생성"""
    print_header("테스트 리포트 생성")

    print_info(f"리포트 생성 중 (제목: {title})...")

    # Use venv's python directly to avoid shell source issues
    venv_python = BACKEND_DIR / ".venv" / "bin" / "python"
    cmd = f'bash -c "cd \\"{BACKEND_DIR}\\" && \\"{venv_python}\\" tools/test_report_generator.py --title \\"{title}\\""'

    print_info(f"실행 명령어: {cmd}")
    print_info("=" * 50)

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print_info("리포트 생성 로그:")
    print_info("=" * 50)

    # 실시간 로그 출력
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(f"  {line.rstrip()}")

    process.wait()
    print_info("=" * 50)

    if process.returncode == 0:
        print_success("테스트 리포트 생성 완료")

        # 최신 리포트 파일 찾기
        reports_dir = BACKEND_DIR / "test_reports"
        md_files = sorted(reports_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)

        if md_files:
            latest_md = md_files[0]
            print_success(f"MD 리포트: {latest_md}")

            # PDF도 확인
            latest_pdf = latest_md.with_suffix('.pdf')
            if latest_pdf.exists():
                print_success(f"PDF 리포트: {latest_pdf}")

        return True
    else:
        print_error(f"리포트 생성 실패 (종료 코드: {process.returncode})")
        return False

def cleanup():
    """서버 종료"""
    print_header("서버 종료 및 정리")

    for name, process in processes.items():
        if process is not None:
            print_info(f"{name} 서버 종료 중 (PID: {process.pid})...")
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
            print_success(f"{name} 서버 종료 완료")

    # killall로 남은 프로세스 종료
    os.system("killall npm 2>/dev/null || true")
    os.system("killall node 2>/dev/null || true")

    print_success("모든 서버 종료 완료")

def main():
    """메인 실행 함수"""
    print_header("🚀 완전 자동화 테스트 + 리포트 생성")

    # 정리 함수 등록
    atexit.register(cleanup)

    # 1. 백엔드 시작
    if not start_backend():
        print_error("백엔드 시작 실패")
        return False

    time.sleep(2)

    # 2. 프론트엔드 시작
    if not start_frontend():
        print_error("프론트엔드 시작 실패")
        return False

    time.sleep(3)

    # 3. E2E 테스트 실행
    if not run_e2e_tests():
        print_error("E2E 테스트 실패")
        return False

    time.sleep(2)

    # 4. 리포트 생성
    report_title = sys.argv[1] if len(sys.argv) > 1 else "GCP UI/UX Implementation - Complete Test Report"
    if not generate_report(report_title):
        print_error("리포트 생성 실패")
        return False

    print_header("✅ 모든 작업 완료!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
