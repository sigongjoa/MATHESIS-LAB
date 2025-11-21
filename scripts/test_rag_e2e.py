import asyncio
import sys
import os
from pathlib import Path

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.rag.parser_service import ParserService
from backend.app.services.rag.embedding_service import EmbeddingService
from backend.app.services.rag.vector_store import VectorStore

async def main():
    print("🚀 Starting End-to-End RAG Indexing & Query Test...\n")
    
    # 0. Clean up local storage to prevent dimension mismatch
    import shutil
    if os.path.exists("qdrant_local_storage"):
        try:
            shutil.rmtree("qdrant_local_storage")
            print("🧹 Cleaned up existing local storage.")
        except Exception as e:
            print(f"⚠️ Failed to clean up storage: {e}")

    # 1. Initialize Services
    parser_service = ParserService()
    embedding_service = EmbeddingService(use_ollama=True) # Local Ollama
    vector_store = VectorStore()
    
    # Ensure Collection Exists
    await vector_store.initialize_collection()
    
    # 2. Parse PDF
    pdf_file = Path("asset/[별책8]+수학과+교육과정.pdf")
    if not pdf_file.exists():
        print(f"❌ File not found: {pdf_file}")
        return

    print(f"📄 Parsing {pdf_file.name}...")
    chunks = await parser_service.parse_document(
        pdf_file, 
        "curriculum", 
        {"policy_version": "2022개정", "subject": "수학"}
    )
    print(f"✅ Parsed {len(chunks)} chunks.")
    
    # 3. Generate Embeddings & Index
    print("🔢 Generating Embeddings & Indexing (This may take a moment)...")
    
    # Batch processing to avoid memory issues
    batch_size = 10
    total_indexed = 0
    
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        texts = [c.content for c in batch_chunks]
        
        # Embed
        embeddings = await embedding_service.embed_batch(texts)
        
        # Prepare for Qdrant
        points = []
        import uuid
        for j, chunk in enumerate(batch_chunks):
            # Qdrant Local Mode requires UUID or Integer IDs
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"math_curriculum_{i+j}"))
            points.append((
                point_id,                 # ID (UUID)
                embeddings[j],            # Vector
                chunk.metadata,           # Metadata
                chunk.content             # Payload
            ))
        
        # Upsert
        await vector_store.upsert_batch(points)
        total_indexed += len(points)
        print(f"   Indexed {total_indexed}/{len(chunks)}...", end='\r')
        
    print(f"\n✅ Successfully indexed {total_indexed} chunks into Qdrant.")
    
    # 4. Query Test
    print("\n🔍 Running Query Tests...\n")
    
    test_queries = [
        "초등학교 1~2학년 수와 연산 영역의 성취기준은 무엇인가요?",
        "수학과 교육과정의 성격은 무엇인가요?",
        "평가 방법 및 유의 사항에 대해 알려주세요"
    ]
    
    for query in test_queries:
        print(f"❓ Query: {query}")
        
        # Embed Query
        query_vector = await embedding_service.get_embedding(query)
        
        # Search
        results = await vector_store.search(query_vector, top_k=3)
        
        print(f"   Found {len(results)} results:")
        for k, res in enumerate(results):
            score = res.score
            content_preview = res.content[:100].replace('\n', ' ')
            meta = res.metadata
            code = meta.get('achievement_code', 'N/A')
            print(f"   [{k+1}] Score: {score:.4f} | Code: {code} | {content_preview}...")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
