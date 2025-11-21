# RAG End-to-End 테스트 실패 분석 보고서 (Local Storage 이슈)

**테스트 일시**: 2025-11-21
**상태**: ❌ **실패 (Failure)**

---

## 1. 실패 원인 분석

*   **오류 메시지**: `ValueError: could not broadcast input array from shape (768,) into shape (3072,)`
*   **현상**: 임베딩 벡터의 차원(768)과 저장소의 벡터 차원(3072)이 맞지 않음.
*   **원인**:
    *   Qdrant Local Mode는 파일 기반 저장소(`qdrant_local_storage`)를 사용합니다.
    *   이전 실행에서 3072차원으로 초기화된 저장소 파일이 디스크에 남아있습니다.
    *   코드에서 768로 설정을 변경했지만, 이미 생성된 파일(`collection.json` 등)은 3072 설정을 유지하고 있어 충돌이 발생했습니다.
    *   `Remove-Item` 명령어가 실패하여(파일이 없거나 권한 문제 등) 초기화가 제대로 되지 않았습니다.

## 2. 해결 방안

**저장소 폴더를 강제로 삭제**하고 다시 실행해야 합니다.

1.  **폴더 확인**: `backend/qdrant_local_storage` 또는 `./qdrant_local_storage` 위치 확인.
2.  **강제 삭제**: Python 스크립트 내에서 `shutil.rmtree`를 사용하여 확실하게 삭제 후 재생성.

---

**결론**: 기존 데이터 파일이 남아있어서 생긴 문제입니다. 스크립트 시작 부분에 **"기존 저장소 삭제 로직"**을 추가하여 해결하겠습니다.
