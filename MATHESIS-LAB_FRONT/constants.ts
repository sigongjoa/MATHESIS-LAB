
import { Curriculum } from './types';

export const API_BASE_URL = '/api/v1';

// Legacy mock data - Resource type for UI development only
interface Resource {
    id: string;
    type: string;
    title: string;
}

export const MOCK_RESOURCES: Resource[] = [
    { id: 'res1', type: 'book', title: 'Calculus: Early Transcendentals, 8th Edition' },
    { id: 'res2', type: 'video', title: 'Essence of calculus, chapter 1 by 3Blue1Brown' },
    { id: 'res3', type: 'article', title: 'A History of the Concept of Derivative' },
    { id: 'res4', type: 'article', title: 'On the Concept of Function' },
    { id: 'res5', type: 'book', title: 'Spivak, M. (1994). Calculus.' },
    { id: 'res6', type: 'video', title: 'Linear Algebra by Gilbert Strang' },
];

// Legacy mock data - simplified curriculum structure for UI development
// This doesn't match the full Node type but is used for display purposes
interface LegacyNode {
    id: string;
    title: string;
    content: string;
    linkedResources: string[];
}

interface LegacyCurriculum {
    id: string;
    title: string;
    description: string;
    icon: string;
    author: string;
    image: string;
    nodes: LegacyNode[];
}

export const MOCK_CURRICULUMS: LegacyCurriculum[] = [
    {
        id: '1',
        title: '고등 미적분 I 심화 과정',
        description: '미분과 적분의 핵심 개념을 문제 풀이 중심으로 학습합니다.',
        icon: 'calculate',
        author: 'John Doe',
        image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDzmavq-y81pcsnIBDiakB9P3QKd7bLXHgW3GM7Z9sF-ccTe_SepOb4WBCF4SIAV6Gef_h_QPb6gTmuIQo3DIM6qdCSpk1iH_d9Nu-kLm6DT7KFvSi-jrowwcwLov34__hjCb2EMKlSjKbS_FzlYIa1Qo1KHc-Kg2-4cyvBV3Wq0jGzvHxRRJYmgtp6oeX4NzKzcUt6ioTbDAXxB49EYEh8Bpi4_BQ23jETZCYjnEkD94FMLUK5WVifwYt7Keyp3bfigqtcrX0apL0',
        nodes: [
            {
                id: '101',
                title: 'Introduction to Derivatives',
                content: `## What is a Derivative?

A derivative is a fundamental concept in calculus that measures the **instantaneous rate of change** of a function. Imagine you're driving a car. Your speed at any given moment is a derivative – it's the rate at which your position is changing with respect to time.

### Key Ideas:
- **Slope of a Tangent Line:** Geometrically, the derivative of a function at a point is the slope of the line tangent to the function's graph at that point.
- **Limits:** The concept of a derivative is formally defined using limits. It's the limit of the average rate of change as the interval shrinks to zero.

### Formula
The derivative of a function f(x) with respect to x is denoted as f'(x) or dy/dx, and is defined as:
\`\`\`
f'(x) = lim(h -> 0) [f(x + h) - f(x)] / h
\`\`\``,
                linkedResources: ['res1', 'res2', 'res3'],
            },
             {
                id: '102',
                title: 'Rules of Differentiation',
                content: '## Basic Differentiation Rules...',
                linkedResources: ['res1', 'res5'],
            },
        ],
    },
    {
        id: '2',
        title: '기초 확률과 통계',
        description: '데이터 분석의 기초가 되는 확률 이론과 통계적 추론을 다룹니다.',
        icon: 'functions',
        author: 'Jane Smith',
        image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBpCjzZeS_GisdsLl8OF3sC4bbGWayc21nRXi4I--fTZEbgKLKL8jMO9cTpZIOcuYFQnNaeE_uFWqpJefCPl151t1-K3aGWv9ji76u9Ny9WPHmiw69hpPeL82g1AHiHVF5dF_RfsE2Q4HWoNLCioqSsphPzVonG9J4dGsMTCbYdgK6KFVoFMqwEMwcIZ4chbxUoVEzm5mhyvbK-vyC-q6wuCmeqeo_dVU_Wf1OFK0wQfYF-N1EYZfksWBLFgGkI2_nRbIBBYzGp7OI',
        nodes: [],
    },
    {
        id: '3',
        title: '중등 기하학 완전 정복',
        description: '도형의 성질과 증명, 공간 지각 능력 향상을 위한 종합 과정입니다.',
        icon: 'square_foot',
        author: 'Alex Johnson',
        image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuB6uGaMHmdti2G6zO4bs7X2YbHn1uBG_1KvIewR7aR7WM-ESQ_Ec6AmE4Cqg5_L-Zx66n1ZaY9X6pBvN1Xw5MT53fyKFcpHBe1VZhAZaYMInIShTGQL7i4iVY4jLKQCJH6x8s9vMTbMhU3DDXwOeFoEpYxt8vZzFyYA3YnE5TsdE4pHDJBg6Z_rzKrQPkwYnPVJmqKIlU0audrqh4Bi0qRg47dHHdPgVxNXeQHPSgcA2WHVeXMXl30Shx0hMvROxeeInVlTkL1OgKE',
        nodes: [],
    },
    {
        id: '4',
        title: '데이터 구조와 알고리즘',
        description: '컴퓨터 과학의 기본이 되는 효율적인 데이터 관리 및 문제 해결 방법을 학습합니다.',
        icon: 'data_object',
        author: 'Emily White',
        image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC1qDsXHVODpReL_wqBmi_O0vguhAdw9oUqXKiGxDU90Vjf7I5ng0PmubkQuRZGY-VSrshx5e4f3U4mpDDf5F-NMj7E3Cjf5u2QguH-iGuH8fz16m1Vv__dG-MXeQF53sfPRCgU23NOxhFn9KJVMKGu_NrykwwSPSRufe-4ImTYpB4vSLwYQLnTr8Lj64gadpKscx4vPCMn5mwVGHey-uuwmQf4IQv3DRB6Y58f6X8OZ6lTFYoodwr7MkPkljgVRffmAo0i4Z3P6ts',
        nodes: [],
    },
     {
        id: '5',
        title: '이산수학',
        description: '논리, 집합, 그래프 이론 등 컴퓨터 과학의 수학적 기초를 다룹니다.',
        icon: 'hub',
        author: 'Michael Brown',
        image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBbUw5w_5JI39gAxP7plz9iy8X0Mjp9uo9VROZ9FbCS7mQpUxu_WOFOsZo6H6OhkzlB-CcX2wOEZEH7hwJ7Zlz1rmGKCYreIzbaDnLEKh4_sJ5Qv2PmlSKSXQY9VbVyXsT0B1hi5t7fyGk1VQURwU2by9BGG4CFKsmNGZKgIryVKdh18WwZ1d1VvbZP8znClpaFLm5WifZjuLhqmDk-qVsHbXW6NGpel-AG-GsCxUOlKX3lVL59AKpXiVgfmNgXOH2LcqYMWyKvY-Y',
        nodes: [],
    },
    {
        id: '6',
        title: '정수론 기초',
        description: '암호학과 순수수학의 기반이 되는 정수의 성질을 탐구합니다.',
        icon: 'pin',
        author: 'Sarah Green',
        image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDkZbjuo2pH4E3dscUEW0H50az8jS07pzZg1nCq5nTupx9rcWGKcNzkjhs2I-UB2g-0OFis-QIn3OtFyRJ1BgHisUEbrSTyR1h5XYww-SWoT3jl2ZhcEgFsVTOV54zXgf5mSfY5HqPgdDZ91PQ1kLhDTa6I71tg3-CNxdOXMCi_hMHPtWvlv3ks3rRv2oAJOoxZ27ds4Z5O4au1iL-dTPBqYUU1CuZrw2qGroQe_M8zlTHsiI9qA0NSkEfQwEuKX7InVqK49Sp5oPY',
        nodes: [],
    }
];
