# 단위 테스트 코드 (Unit Test Code)

## 1. 개요
이 문서는 'MATHESIS LAB' 프로젝트의 단위 테스트 코드 작성 전략 및 예시를 제공합니다. TDD(Test-Driven Development) 방법론에 따라 각 기능의 최소 단위를 검증하는 테스트 코드를 작성하며, 백엔드(Python)는 Pytest, 프론트엔드(React)는 Jest를 활용합니다.

## 2. 백엔드 단위 테스트 (Python / Pytest)

### 2.1. 테스트 환경 설정
*   **의존성 설치:**
    ```bash
    pip install pytest pytest-mock httpx
    ```
*   **테스트 파일 구조:**
    *   `backend/tests/unit/`
        *   `test_auth_service.py`
        *   `test_curriculum_service.py`
        *   `test_node_service.py`
        *   `test_zotero_integration.py`
        *   `test_ai_integration.py`
        *   ...

### 2.2. 예시: Zotero 연동 서비스 테스트 (`test_zotero_integration.py`)

이 테스트는 `ZoteroService`가 외부 Zotero API와 올바르게 상호작용하는지 검증합니다. `pytest-mock`을 사용하여 외부 HTTP 요청을 Mocking합니다.

```python
# backend/tests/unit/test_zotero_integration.py
import pytest
from unittest.mock import MagicMock
import httpx # FastAPI에서 비동기 HTTP 클라이언트로 httpx를 사용할 수 있음

# 실제 ZoteroService 클래스는 backend/app/services/zotero_service.py 에 있다고 가정
# from app.services.zotero_service import ZoteroService

# 테스트를 위한 가상의 ZoteroService (실제 구현 시에는 위 주석 해제)
class ZoteroService:
    def __init__(self, base_url="http://localhost:8000/zotero"):
        self.base_url = base_url

    async def search_by_tag(self, tag_name: str):
        # 실제 구현에서는 httpx.AsyncClient 등을 사용할 수 있음
        # 여기서는 테스트를 위해 동기 requests.get을 사용하거나,
        # 비동기 테스트를 위해 httpx.AsyncClient를 mocking해야 함.
        # 편의상 동기 requests.get을 가정하고 mocking 진행.
        response = httpx.get(f"{self.base_url}/items", params={"tag": tag_name})
        response.raise_for_status()
        return response.json()

@pytest.mark.asyncio # 비동기 함수 테스트를 위한 마커 (pytest-asyncio 필요)
async def test_search_zotero_by_tag_success(mocker):
    """
    TC-ZT-001: '난류' 태그로 Zotero 문헌 검색 성공 시나리오
    """
    mock_items = [
        {"zotero_key": "key1", "title": "Item A", "authors": ["Author1"], "publication_year": 2023, "tags": ["난류"]},
        {"zotero_key": "key2", "title": "Item B", "authors": ["Author2"], "publication_year": 2022, "tags": ["난류", "유체역학"]},
        {"zotero_key": "key3", "title": "Item C", "authors": ["Author3"], "publication_year": 2021, "tags": ["난류"]},
    ]

    # httpx.get 함수를 mocking
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_items
    mock_response.raise_for_status.return_value = None # 예외 발생 안 함

    mocker.patch('httpx.get', return_value=mock_response)

    service = ZoteroService()
    results = await service.search_by_tag("난류")

    assert len(results) == 3
    assert all("난류" in item["tags"] for item in results)
    assert results[0]["title"] == "Item A"
    httpx.get.assert_called_once_with("http://localhost:8000/zotero/items", params={"tag": "난류"})

@pytest.mark.asyncio
async def test_search_zotero_by_tag_no_results(mocker):
    """
    TC-ZT-002: 존재하지 않는 태그로 Zotero 문헌 검색 시 결과 없음 시나리오
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None

    mocker.patch('httpx.get', return_value=mock_response)

    service = ZoteroService()
    results = await service.search_by_tag("ABCDEFG")

    assert len(results) == 0
    httpx.get.assert_called_once_with("http://localhost:8000/zotero/items", params={"tag": "ABCDEFG"})

@pytest.mark.asyncio
async def test_search_zotero_by_tag_http_error(mocker):
    """
    Zotero API 호출 시 HTTP 오류 발생 시나리오
    """
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=httpx.Request("GET", "http://localhost:8000/zotero/items"), response=mock_response
    )

    mocker.patch('httpx.get', return_value=mock_response)

    service = ZoteroService()
    with pytest.raises(httpx.HTTPStatusError):
        await service.search_by_tag("난류")
```

### 2.3. 테스트 실행
```bash
pytest backend/tests/unit/test_zotero_integration.py
```

## 3. 프론트엔드 단위 테스트 (React / Jest)

### 3.1. 테스트 환경 설정
*   **의존성 설치 (Create React App 기준):**
    ```bash
    npm install --save-dev @testing-library/react @testing-library/jest-dom jest-environment-jsdom
    ```
*   **테스트 파일 구조:**
    *   `frontend/src/__tests__/`
        *   `CurriculumMap.test.tsx`
        *   `NodeEditor.test.tsx`
        *   `ZoteroSearch.test.tsx`
        *   `AiAssistant.test.tsx`
        *   ...

### 3.2. 예시: Zotero 검색 컴포넌트 테스트 (`ZoteroSearch.test.tsx`)

이 테스트는 Zotero 검색 컴포넌트가 사용자 입력에 따라 검색을 수행하고 결과를 올바르게 표시하는지 검증합니다. `react-testing-library`를 사용하여 컴포넌트를 렌더링하고 사용자 이벤트를 시뮬레이션합니다.

```typescript jsx
// frontend/src/__tests__/ZoteroSearch.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ZoteroSearch from '../components/ZoteroSearch'; // 실제 컴포넌트 경로

// API 호출을 Mocking
const mockZoteroApi = {
  searchByTag: jest.fn(),
};

// ZoteroSearch 컴포넌트가 이 mock API를 사용하도록 설정 (예: Context API 또는 Prop Drilling)
// 여기서는 간단하게 컴포넌트 내부에서 fetch 등을 mocking하는 방식으로 가정
// 실제 구현에서는 Jest의 mock module 기능을 활용하여 API 모듈 자체를 mocking하는 것이 일반적

describe('ZoteroSearch Component', () => {
  beforeEach(() => {
    // 각 테스트 전에 mock 함수 초기화
    mockZoteroApi.searchByTag.mockClear();
  });

  test('renders search input and button', () => {
    render(<ZoteroSearch onSelectZoteroItem={() => {}} />);
    expect(screen.getByPlaceholderText(/태그로 Zotero 문헌 검색/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /검색/i })).toBeInTheDocument();
  });

  test('displays search results when API call is successful', async () => {
    const mockResults = [
      { zotero_key: 'key1', title: 'Item A', authors: ['Author1'], publication_year: 2023, tags: ['난류'] },
      { zotero_key: 'key2', title: 'Item B', authors: ['Author2'], publication_year: 2022, tags: ['난류', '유체역학'] },
    ];
    mockZoteroApi.searchByTag.mockResolvedValue(mockResults);

    // fetch API를 mocking
    jest.spyOn(global, 'fetch').mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResults),
      } as Response)
    );

    render(<ZoteroSearch onSelectZoteroItem={() => {}} />);

    const searchInput = screen.getByPlaceholderText(/태그로 Zotero 문헌 검색/i);
    fireEvent.change(searchInput, { target: { value: '난류' } });
    fireEvent.click(screen.getByRole('button', { name: /검색/i }));

    await waitFor(() => {
      expect(screen.getByText('Item A (Author1, 2023)')).toBeInTheDocument();
      expect(screen.getByText('Item B (Author2, 2022)')).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/zotero/items?tag=난류'));
  });

  test('displays "No results found" when API returns empty array', async () => {
    mockZoteroApi.searchByTag.mockResolvedValue([]);

    jest.spyOn(global, 'fetch').mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      } as Response)
    );

    render(<ZoteroSearch onSelectZoteroItem={() => {}} />);

    const searchInput = screen.getByPlaceholderText(/태그로 Zotero 문헌 검색/i);
    fireEvent.change(searchInput, { target: { value: '존재하지않는태그' } });
    fireEvent.click(screen.getByRole('button', { name: /검색/i }));

    await waitFor(() => {
      expect(screen.getByText(/검색 결과가 없습니다/i)).toBeInTheDocument();
    });
  });

  test('calls onSelectZoteroItem when an item is selected', async () => {
    const mockResults = [
      { zotero_key: 'key1', title: 'Item A', authors: ['Author1'], publication_year: 2023, tags: ['난류'] },
    ];
    const mockOnSelect = jest.fn();

    jest.spyOn(global, 'fetch').mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResults),
      } as Response)
    );

    render(<ZoteroSearch onSelectZoteroItem={mockOnSelect} />);

    const searchInput = screen.getByPlaceholderText(/태그로 Zotero 문헌 검색/i);
    fireEvent.change(searchInput, { target: { value: '난류' } });
    fireEvent.click(screen.getByRole('button', { name: /검색/i }));

    await waitFor(() => {
      fireEvent.click(screen.getByText('Item A (Author1, 2023)'));
    });

    expect(mockOnSelect).toHaveBeenCalledWith(mockResults[0]);
  });
});
```

### 3.3. 테스트 실행
```bash
npm test frontend/src/__tests/ZoteroSearch.test.tsx
```

## 4. TDD 워크플로우 요약
1.  **테스트 케이스 선택:** `docs/tdd/test_cases/README.md`에서 구현할 기능에 해당하는 테스트 케이스를 선택합니다.
2.  **테스트 코드 작성 (Red):** 선택한 테스트 케이스를 검증하는 단위 테스트 코드를 작성합니다. 이 코드는 아직 기능이 구현되지 않았으므로 실패해야 합니다.
3.  **테스트 실행 및 실패 확인:** 테스트를 실행하여 실패(Red)하는 것을 확인합니다.
4.  **기능 코드 작성 (Green):** 테스트를 통과시킬 수 있는 최소한의 기능 코드를 작성합니다.
5.  **테스트 실행 및 성공 확인:** 테스트를 다시 실행하여 성공(Green)하는 것을 확인합니다.
6.  **리팩토링 (Refactor):** 기능 코드를 개선하고, 중복을 제거하며, 가독성을 높입니다. 리팩토링 후에도 모든 테스트가 성공하는지 확인합니다.
7.  **반복:** 다음 테스트 케이스에 대해 1단계부터 반복합니다.
