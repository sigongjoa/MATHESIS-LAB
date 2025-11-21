# 범용 교과과정 파싱 모델 (Universal Curriculum Parsing Model)

이 문서는 수학과뿐만 아니라 국어, 영어, 사회, 과학 등 **모든 교과목의 교육과정 문서**를 처리할 수 있는 추상화된 파싱 모델을 정의합니다.

## 1. 추상화 배경 (Abstraction Context)

대한민국의 모든 교과 교육과정 문서는 **교육부 고시**라는 공통된 표준 양식을 따릅니다. 과목 내용은 다르지만, 문서를 구성하는 **골격(Skeleton)**과 **위계(Hierarchy)**는 동일합니다. 따라서 하나의 범용 모델로 모든 과목을 커버할 수 있습니다.

## 2. 공통 구조 (Common Structure)

모든 교과목 문서는 다음과 같은 공통 위계를 가집니다. 이를 `CurriculumHierarchy`로 정의합니다.

| 레벨 | 추상화 명칭 (Abstract Name) | 예시 (수학) | 예시 (국어) | 예시 (영어) |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | **School Level** (학교급) | 초/중/고 | 초/중/고 | 초/중/고 |
| **L2** | **Grade Cluster** (학년군) | 1~2학년군 | 1~2학년군 | 3~4학년군 |
| **L3** | **Domain/Category** (영역) | 수와 연산 | 듣기·말하기 | 읽기 |
| **L4** | **Standard Code** (성취기준) | `[2수01-01]` | `[2국01-01]` | `[4영02-01]` |
| **L5** | **Attributes** (속성) | 해설, 교수학습, 평가 | 해설, 교수학습, 평가 | 해설, 교수학습, 평가 |

## 3. 범용 데이터 모델 (Universal Data Model)

모든 교과목 데이터를 수용할 수 있는 유연한 스키마입니다.

```json
{
  "metadata": {
    "subject": "String (e.g., 수학, 국어, 영어)",
    "policy_year": "String (e.g., 2022개정)",
    "school_level": "Enum (ELEMENTARY, MIDDLE, HIGH)",
    "grade_cluster": "String (e.g., 1~2학년군)",
    "domain": "String (e.g., 수와 연산, 읽기)"
  },
  "standard": {
    "code": "String (Unique ID, e.g., [12화학Ⅰ03-02])",
    "content": "String (성취기준 본문)"
  },
  "attributes": {
    "explanation": "String (성취기준 해설)",
    "teaching_guide": "List<String> (교수·학습 방법 및 유의 사항)",
    "evaluation_guide": "List<String> (평가 방법 및 유의 사항)",
    "keywords": "List<String> (핵심어, e.g., 화학결합, 공유결합)"
  }
}
```

## 4. 과목별 특이사항 처리 (Subject-Specific Strategy)

추상화 모델 위에서 과목별로 달라지는 부분은 **설정(Configuration)**으로 주입합니다.

### 4.1. 성취기준 코드 패턴 (Regex Configuration)
과목마다 코드의 약어가 다르므로, 이를 동적으로 처리합니다.

*   **Base Pattern**: `\[(\d+)(SUBJECT_CODE)(\d+-\d+)\]`
*   **Subject Codes**:
    *   수학: `수`, `수학`, `대수`, `미적`, `기하`, `확통` ...
    *   국어: `국`, `화작`, `독서`, `언매`, `문학` ...
    *   영어: `영`, `영어`, `영회`, `영독` ...
    *   과학: `과`, `물`, `화`, `생`, `지` ...

### 4.2. 영역(Domain) 키워드 매핑
과목별로 사용하는 영역의 용어가 다를 수 있습니다.

```python
DOMAIN_KEYWORDS = {
    "MATH": ["수와 연산", "변화와 관계", "도형", "측정", "자료와 가능성"],
    "KOREAN": ["듣기·말하기", "읽기", "쓰기", "문법", "문학", "매체"],
    "ENGLISH": ["듣기", "말하기", "읽기", "쓰기"],
    "SCIENCE": ["운동과 에너지", "물질", "생명", "지구와 우주"]
}
```

## 5. 확장성 설계 (Extensibility)

이 모델은 다음과 같은 확장이 가능합니다.

1.  **역량(Competency) 매핑**:
    *   2022 개정 교육과정은 '교과 역량'을 강조합니다.
    *   파싱 시 해당 성취기준이 어떤 역량(예: 의사소통, 정보처리)과 연결되는지 텍스트 분석을 통해 태깅할 수 있습니다.
2.  **선수/후수 학습 연결 (Prerequisite Linking)**:
    *   성취기준 코드를 분석하여 `[2수...]` -> `[4수...]` 와 같이 학년 간의 연계성을 그래프로 구축할 수 있습니다.
    *   예: "이 내용을 배우려면 2학년 때 뭘 배웠어야 하지?"에 대한 답을 줄 수 있습니다.

## 6. 결론

우리는 **"수학"**이라는 구체적인 인스턴스로 시작하지만, 시스템의 코어는 **"교육과정(Curriculum)"**이라는 추상 클래스를 처리하도록 설계합니다.

*   `CurriculumParser` (Abstract Base Class)
    *   `MathParser` (Impl)
    *   `KoreanParser` (Impl)
    *   `EnglishParser` (Impl)

이렇게 하면 새로운 과목이 추가될 때마다 파서 전체를 새로 짜는 게 아니라, **Regex 패턴과 키워드 설정만 갈아끼우면(Plug-in)** 바로 대응이 가능합니다.
