#!/bin/bash

# RAG 시스템 테스트 실행 스크립트

cd "$(dirname "$0")/.."

# 가상환경 활성화
source .venv/bin/activate

# PYTHONPATH 설정
export PYTHONPATH=$(pwd)

echo "========================================="
echo "RAG System Test Suite"
echo "========================================="
echo ""

# 1. Parser Service 테스트
echo "1. Testing Parser Service..."
pytest backend/tests/unit/test_parser_service.py -v --tb=short

# 2. Vector Store 테스트
echo ""
echo "2. Testing Vector Store..."
pytest backend/tests/unit/test_vector_store.py -v --tb=short

# 3. Embedding Service 테스트
echo ""
echo "3. Testing Embedding Service..."
pytest backend/tests/unit/test_embedding_service.py -v --tb=short

# 4. RAG Service 테스트
echo ""
echo "4. Testing RAG Service..."
pytest backend/tests/unit/test_rag_service.py -v --tb=short

# 전체 요약
echo ""
echo "========================================="
echo "Running All RAG Tests..."
echo "========================================="
pytest backend/tests/unit/test_parser_service.py \
       backend/tests/unit/test_vector_store.py \
       backend/tests/unit/test_embedding_service.py \
       backend/tests/unit/test_rag_service.py \
       -v --tb=short --cov=backend/app/services/rag --cov-report=term-missing

echo ""
echo "========================================="
echo "Test Suite Complete!"
echo "========================================="
