# RAG End-to-End 테스트 결과 보고서

**테스트 일시**: 2025-11-21
**테스트 환경**: WSL (Ubuntu), Python 3.x Virtual Environment
**대상**: PDF 파싱 -> 임베딩(Ollama) -> Vector DB(Qdrant) -> 검색

---

## 1. 테스트 요약

| 단계 | 결과 | 상세 |
| :--- | :--- | :--- |
| **1. 파싱** | ✅ **성공** | 491개 청크 생성 완료 |
| **2. 임베딩** | ❌ **실패** | Ollama 연결 실패 (404 Not Found) |
| **3. 인덱싱** | ❌ **실패** | Qdrant 클라이언트 연결 실패 (ImportError or Connection Error) |
| **4. 검색** | ❌ **실패** | 결과 0건 반환 |

## 2. 원인 분석

### 2.1. Ollama 연결 오류 (404 Not Found)
*   로그: `Ollama embedding failed: Client error '404 Not Found' for url 'http://localhost:11434/api/embeddings'`
*   원인:
    1.  WSL 내부에서 윈도우의 Ollama(localhost:11434)에 접근하지 못하고 있음.
    2.  또는 Ollama 모델(`nomic-embed-text` 등)이 로드되지 않았거나 API 엔드포인트가 다름.

### 2.2. Qdrant 클라이언트 오류
*   로그: `Qdrant client not available, skipping batch upsert`
*   원인: `qdrant-client` 라이브러리가 설치되어 있지 않거나, Docker 컨테이너(Qdrant)가 실행 중이지 않음.

## 3. 조치 계획

1.  **라이브러리 설치**: `pip install qdrant-client httpx`
2.  **Ollama 점검**:
    *   윈도우에서 `ollama serve` 실행 확인.
    *   WSL에서 `curl http://host.docker.internal:11434` 등으로 접근 테스트.
    *   필요 시 `OLLAMA_HOST` 환경변수 설정.
3.  **Qdrant 점검**:
    *   Docker 컨테이너 실행 확인 (`docker ps`).

---

**결론**: 코드 로직(파싱, 스크립트)은 정상이지만, **실행 환경(인프라/네트워크)** 문제로 인해 데이터가 실제로 DB에 들어가지 않았습니다. 환경 설정 후 재시도가 필요합니다.
