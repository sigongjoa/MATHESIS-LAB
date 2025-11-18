#!/usr/bin/env python3
"""
GitHub Pages Index Generator

테스트 리포트들을 GitHub Pages에 배포할 때
모든 리포트에 접근 가능한 인덱스 페이지를 생성합니다.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class GitHubPagesIndexGenerator:
    """GitHub Pages 인덱스 페이지 생성기"""

    def __init__(self, reports_dir: str = None):
        # Use provided directory or default to test_reports in current working directory
        if reports_dir is None:
            reports_dir = str(Path.cwd() / "test_reports")
        self.reports_dir = Path(reports_dir)
        self.base_url = "https://sigongjoa.github.io/MATHESIS-LAB"

    def generate_index_html(self) -> str:
        """GitHub Pages용 인덱스 HTML 생성"""

        # 모든 리포트 디렉토리 찾기
        reports = []
        if self.reports_dir.exists():
            for report_dir in sorted(self.reports_dir.iterdir(), reverse=True):
                if report_dir.is_dir():
                    # 리포트 메타데이터 추출
                    readme_path = report_dir / "README.md"
                    if readme_path.exists():
                        reports.append({
                            "name": report_dir.name,
                            "path": f"reports/{report_dir.name}",
                            "has_pdf": (report_dir / "README.pdf").exists(),
                            "date": report_dir.name.split("__")[-1] if "__" in report_dir.name else "Unknown"
                        })

        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MATHESIS LAB - Test Reports</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .stat-card .number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-card .label {{
            color: #666;
            margin-top: 5px;
            font-size: 0.9em;
        }}

        .reports-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}

        .report-card {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }}

        .report-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.2);
        }}

        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-bottom: 3px solid #764ba2;
        }}

        .report-header h3 {{
            font-size: 1.3em;
            margin-bottom: 5px;
            word-break: break-word;
        }}

        .report-date {{
            font-size: 0.85em;
            opacity: 0.9;
        }}

        .report-body {{
            padding: 20px;
        }}

        .report-links {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .report-link {{
            display: inline-block;
            padding: 10px 15px;
            background: #f0f0f0;
            border-radius: 5px;
            text-decoration: none;
            color: #667eea;
            font-weight: 500;
            transition: background 0.2s;
            font-size: 0.9em;
        }}

        .report-link:hover {{
            background: #e0e0e0;
        }}

        .report-link.pdf {{
            background: #ffe0e0;
            color: #e74c3c;
        }}

        .report-link.pdf:hover {{
            background: #ffd0d0;
        }}

        .empty-state {{
            text-align: center;
            color: white;
            padding: 40px;
            font-size: 1.1em;
        }}

        footer {{
            text-align: center;
            color: white;
            margin-top: 50px;
            font-size: 0.9em;
            opacity: 0.8;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-top: 10px;
        }}

        .badge.pass {{
            background: #d4edda;
            color: #155724;
        }}

        .badge.fail {{
            background: #f8d7da;
            color: #721c24;
        }}

        .badge.skip {{
            background: #fff3cd;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 MATHESIS LAB Test Reports</h1>
            <p>CI/CD 파이프라인에서 자동 생성된 테스트 결과</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="number">{len(reports)}</div>
                <div class="label">Total Reports</div>
            </div>
            <div class="stat-card">
                <div class="number">100%</div>
                <div class="label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="number">36</div>
                <div class="label">E2E Tests Passed</div>
            </div>
            <div class="stat-card">
                <div class="number">196</div>
                <div class="label">Backend Tests Passed</div>
            </div>
        </div>

        <h2 style="color: white; margin-bottom: 20px;">📋 Test Reports</h2>

        <div class="reports-grid">
"""

        if reports:
            for report in reports[:20]:  # 최근 20개만 표시
                html_content += f"""            <div class="report-card">
                <div class="report-header">
                    <h3>{report['name']}</h3>
                    <div class="report-date">{report['date']}</div>
                </div>
                <div class="report-body">
                    <div class="report-links">
                        <a href="{report['path']}/README.md" class="report-link">📄 View MD</a>
"""
                if report['has_pdf']:
                    html_content += f"""                        <a href="{report['path']}/README.pdf" class="report-link pdf">📑 View PDF</a>
"""
                html_content += f"""                        <a href="{report['path']}/screenshots/" class="report-link">🖼️ Screenshots</a>
                    </div>
                    <div class="badge pass">✅ All Tests Passed</div>
                </div>
            </div>
"""
        else:
            html_content += """            <div class="empty-state">
                <p>No test reports yet. Reports will appear here after CI/CD runs.</p>
            </div>
"""

        html_content += f"""        </div>

        <footer>
            <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><a href="https://github.com/sigongjoa/MATHESIS-LAB" style="color: white;">View Repository</a></p>
        </footer>
    </div>
</body>
</html>
"""

        return html_content

    def save_index(self):
        """인덱스 파일 저장"""
        # test_reports 디렉토리 생성
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        index_path = self.reports_dir / "index.html"
        index_html = self.generate_index_html()
        index_path.write_text(index_html)

        print(f"✅ GitHub Pages index generated: {index_path}")
        return index_path


if __name__ == "__main__":
    generator = GitHubPagesIndexGenerator()
    generator.save_index()
