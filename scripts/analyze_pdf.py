#!/usr/bin/env python3
"""
수학과 교육과정 PDF 분석 스크립트
"""

import fitz  # PyMuPDF
import sys

def analyze_pdf(pdf_path):
    """PDF 파일 분석"""
    try:
        doc = fitz.open(pdf_path)
        
        print("=" * 60)
        print("수학과 교육과정 PDF 분석")
        print("=" * 60)
        print(f"\n📄 파일: {pdf_path}")
        print(f"📊 총 페이지 수: {len(doc)}")
        print(f"📖 메타데이터: {doc.metadata}")
        
        # 첫 페이지 샘플
        print("\n" + "=" * 60)
        print("첫 페이지 텍스트 샘플:")
        print("=" * 60)
        first_page = doc[0].get_text()
        print(first_page[:800])
        
        # 성취기준 패턴 찾기
        print("\n" + "=" * 60)
        print("성취기준 코드 샘플 (처음 10개):")
        print("=" * 60)
        
        import re
        achievement_codes = []
        
        for page_num in range(min(50, len(doc))):  # 처음 50페이지만
            text = doc[page_num].get_text()
            codes = re.findall(r'\[(\d+[가-힣]+\d+-\d+)\]', text)
            for code in codes:
                if code not in achievement_codes:
                    achievement_codes.append(code)
                    if len(achievement_codes) >= 10:
                        break
            if len(achievement_codes) >= 10:
                break
        
        for i, code in enumerate(achievement_codes, 1):
            print(f"{i}. [{code}]")
        
        # 페이지별 텍스트 길이
        print("\n" + "=" * 60)
        print("페이지별 텍스트 길이 (처음 10페이지):")
        print("=" * 60)
        
        for page_num in range(min(10, len(doc))):
            text = doc[page_num].get_text()
            print(f"페이지 {page_num + 1}: {len(text)} 문자")
        
        doc.close()
        
        print("\n" + "=" * 60)
        print("분석 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    pdf_path = "asset/[별책8]+수학과+교육과정.pdf"
    analyze_pdf(pdf_path)
