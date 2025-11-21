import asyncio
import sys
import os
from pathlib import Path

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.rag.parser_service import ParserService

async def main():
    print("🚀 Starting Real Parsing Test...\n")
    
    service = ParserService()
    asset_dir = Path("asset")
    
    # 1. Test Math Curriculum PDF
    pdf_file = asset_dir / "[별책8]+수학과+교육과정.pdf"
    if pdf_file.exists():
        print(f"📄 Parsing {pdf_file.name}...")
        chunks = await service.parse_document(
            pdf_file, 
            "curriculum", 
            {"policy_version": "2022개정", "subject": "수학"}
        )
        
        print(f"✅ Generated {len(chunks)} chunks.")
        if chunks:
            print(f"   Sample Chunk 0: {chunks[0].content[:100]}...")
            print(f"   Metadata: {chunks[0].metadata}")
            
            # DoD Verification
            codes = [c.metadata.get('achievement_code') for c in chunks if 'achievement_code' in c.metadata]
            print(f"   Found {len(codes)} achievement codes.")
    else:
        print(f"❌ File not found: {pdf_file}")

    print("-" * 50)

    # 2. Test Operation Plan HWP
    hwp_file = asset_dir / "2025학년도 2학기 3학년 교과별 교수학습 및 평가 운영 계획(수정).hwp"
    if hwp_file.exists():
        print(f"📄 Parsing {hwp_file.name}...")
        chunks = await service.parse_document(
            hwp_file, 
            "school_plan", 
            {"year": "2025", "grade": "3"}
        )
        
        print(f"✅ Generated {len(chunks)} chunks.")
        if chunks:
            print(f"   Sample Chunk 0: {chunks[0].content[:100]}...")
            print(f"   Metadata: {chunks[0].metadata}")
    else:
        print(f"❌ File not found: {hwp_file}")

if __name__ == "__main__":
    asyncio.run(main())
