# RAG End-to-End 테스트 실패 분석 보고서

**테스트 일시**: 2025-11-21
**상태**: ❌ **실패 (Failure)**

---

## 1. 실패 원인 분석

### 1.1. Ollama (임베딩 모델)
*   **상태**: ✅ **해결됨**. `ollama pull nomic-embed-text` 명령이 성공적으로 실행되어 모델이 준비되었습니다.

### 1.2. Qdrant (Vector DB)
*   **상태**: ❌ **연결 거부 (Connection Refused)**
*   **로그**: `qdrant_client.http.exceptions.ResponseHandlingException: [Errno 111] Connection refused`
*   **원인**:
    *   테스트 스크립트가 `http://localhost:6333`으로 접속을 시도했으나 실패함.
    *   WSL 환경에서 Docker 컨테이너(Qdrant)가 실행 중이지 않거나, 포트 포워딩이 제대로 되지 않음.

## 2. 해결 방안

Qdrant 컨테이너를 실행해야 합니다.

1.  **Docker 실행 확인**: 윈도우 Docker Desktop이 실행 중인지 확인.
2.  **Qdrant 컨테이너 시작**:
    ```bash
    docker run -d -p 6333:6333 -p 6334:6334 \
        -v $(pwd)/qdrant_storage:/qdrant/storage:z \
        qdrant/qdrant
    ```
3.  **재테스트**: 컨테이너가 뜬 후 다시 스크립트 실행.

---

**결론**: 코드나 모델의 문제가 아니라, **DB 서버(Qdrant)가 꺼져 있어서** 발생한 문제입니다. DB만 켜면 성공할 것입니다.
