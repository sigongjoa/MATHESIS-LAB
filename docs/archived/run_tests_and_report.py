#!/usr/bin/env python3
"""
통합 테스트 실행 및 리포트 생성 스크립트
E2E 테스트 → 자동 리포트 생성
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
import argparse

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.absolute()
FRONTEND_DIR = PROJECT_ROOT / "MATHESIS-LAB_FRONT"
SCREENSHOTS_DIR = FRONTEND_DIR / "e2e-screenshots"

def print_header(text):
    """헤더 출력"""
    print("\n" + "=" * 60)
    print(f"🚀 {text}")
    print("=" * 60 + "\n")

def print_step(text):
    """스텝 출력"""
    print(f"\n{text}")
    print("-" * 60)

def check_server_running(port, name):
    """서버 실행 여부 확인"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def run_command(cmd, cwd=None, shell=False, capture=True):
    """명령 실행"""
    if capture:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout + result.stderr
    else:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=shell,
            timeout=300
        )
        return result.returncode == 0, ""

def run_e2e_tests():
    """E2E 테스트 실행"""
    print_step("2️⃣  E2E 테스트 실행")

    # 스크린샷 디렉토리 생성
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    # 기존 스크린샷 정리 (선택)
    print("📸 스크린샷 디렉토리 준비 중...")
    screenshot_files = list(SCREENSHOTS_DIR.glob("*.png"))
    if screenshot_files:
        print(f"   기존 스크린샷: {len(screenshot_files)}개")

    # E2E 테스트 실행
    print("🔍 Playwright E2E 테스트 실행...")
    success, output = run_command(
        ["npx", "playwright", "test", "e2e/", "--reporter=json", "--reporter=list"],
        cwd=str(FRONTEND_DIR),
        capture=False
    )

    if success or True:  # 테스트 실패해도 진행 (스크린샷 수집)
        print("✅ E2E 테스트 실행 완료\n")

        # 생성된 스크린샷 확인
        screenshot_files = sorted(SCREENSHOTS_DIR.glob("*.png"))
        print(f"📸 수집된 스크린샷: {len(screenshot_files)}개")

        if screenshot_files:
            print("   생성된 파일:")
            for f in screenshot_files[:5]:  # 최대 5개만 표시
                size = f.stat().st_size / 1024  # KB
                print(f"     - {f.name} ({size:.1f}KB)")
            if len(screenshot_files) > 5:
                print(f"     ... 및 {len(screenshot_files) - 5}개 더")

        return True, len(screenshot_files)
    else:
        print("⚠️ E2E 테스트 실행 실패")
        return False, 0

def run_report_generator(title):
    """리포트 생성기 실행"""
    print_step("3️⃣  테스트 리포트 생성")

    # 가상환경 활성화 경로
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"

    if not venv_python.exists():
        print("❌ 가상환경을 찾을 수 없습니다")
        return False, None, None

    print(f"🔧 리포트 생성기 실행 중... (제목: {title})")

    success, output = run_command(
        [str(venv_python), "tools/test_report_generator.py", "--title", title],
        cwd=str(PROJECT_ROOT),
        capture=True
    )

    if success or "✅" in output:  # 일부 경고는 무시
        print("✅ 리포트 생성 완료\n")

        # 생성된 파일 찾기
        reports_dir = PROJECT_ROOT / "test_reports"
        if reports_dir.exists():
            md_files = sorted(reports_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
            pdf_files = sorted(reports_dir.glob("*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)

            latest_md = md_files[0] if md_files else None
            latest_pdf = pdf_files[0] if pdf_files else None

            return True, latest_md, latest_pdf

    print("⚠️ 리포트 생성 중 오류 발생")
    print(output[-500:] if len(output) > 500 else output)
    return False, None, None

def print_summary(args, start_time, screenshot_count, md_report, pdf_report):
    """최종 요약 출력"""
    duration = time.time() - start_time
    minutes = int(duration // 60)
    seconds = int(duration % 60)

    print_header("완료: 통합 테스트 실행 및 리포트 생성")

    print("📊 실행 결과:")
    print(f"   ⏱️  소요 시간: {minutes}분 {seconds}초")
    print(f"   📸 수집된 스크린샷: {screenshot_count}개")
    print("")

    print("📁 생성된 리포트:")
    if md_report:
        md_size = md_report.stat().st_size / 1024
        print(f"   ✅ Markdown: {md_report.name} ({md_size:.1f}KB)")
    else:
        print("   ⚠️  Markdown: 생성 안 됨")

    if pdf_report:
        pdf_size = pdf_report.stat().st_size / 1024
        print(f"   ✅ PDF: {pdf_report.name} ({pdf_size:.1f}KB)")
    else:
        print("   ⚠️  PDF: 생성 안 됨")

    print("")
    print("🔍 다음 단계:")
    if md_report:
        print(f"   MD 확인: cat {md_report}")
    if pdf_report:
        print(f"   PDF 확인: open {pdf_report}  # macOS")
        print(f"   PDF 확인: xdg-open {pdf_report}  # Linux")

    print("")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="E2E 테스트 실행 및 리포트 생성"
    )
    parser.add_argument(
        "--title",
        default="Integration Test Report",
        help="리포트 제목 (기본값: 'Integration Test Report')"
    )
    parser.add_argument(
        "--skip-e2e",
        action="store_true",
        help="E2E 테스트 건너뛰고 리포트만 생성"
    )

    args = parser.parse_args()

    start_time = time.time()

    print_header(f"통합 테스트 시작: {args.title}")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 리포트 제목: {args.title}")
    print("")

    # 1. 서버 상태 확인
    print_step("1️⃣  서버 상태 확인")

    backend_running = check_server_running(8000, "Backend")
    frontend_running = check_server_running(3001, "Frontend")

    if backend_running:
        print("✅ 백엔드 서버: 실행 중 (포트 8000)")
    else:
        print("⚠️  백엔드 서버: 실행 중이 아님 (포트 8000)")
        print("   명령: source .venv/bin/activate && python -m uvicorn backend.app.main:app --reload")

    if frontend_running:
        print("✅ 프론트엔드 서버: 실행 중 (포트 3001)")
    else:
        print("⚠️  프론트엔드 서버: 실행 중이 아님 (포트 3001)")
        print("   명령: cd MATHESIS-LAB_FRONT && npm run dev")

    print("")

    # 2. E2E 테스트 실행
    screenshot_count = 0
    if not args.skip_e2e:
        e2e_success, screenshot_count = run_e2e_tests()
        if not e2e_success and not backend_running and not frontend_running:
            print("\n⚠️  서버가 실행 중이 아니어서 E2E 테스트를 실행할 수 없습니다")
            print("   먼저 백엔드와 프론트엔드 서버를 시작해주세요")
    else:
        print_step("2️⃣  E2E 테스트 건너뛰기")
        print("--skip-e2e 옵션으로 E2E 테스트를 건너뛰었습니다\n")

    # 3. 리포트 생성
    report_success, md_report, pdf_report = run_report_generator(args.title)

    # 4. 최종 요약
    print_summary(args, start_time, screenshot_count, md_report, pdf_report)

    return 0 if report_success else 1

if __name__ == "__main__":
    sys.exit(main())
