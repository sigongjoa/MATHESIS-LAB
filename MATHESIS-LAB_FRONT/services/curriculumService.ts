
import { Curriculum, CurriculumCreate, CurriculumUpdate, Node, NodeCreate } from '../types';

const API_URL = '/api/v1/curriculums/';

export const getCurriculums = async (): Promise<Curriculum[]> => {
    const response = await fetch(API_URL);
    if (!response.ok) {
        throw new Error('Failed to fetch curriculums');
    }
    return response.json();
};

export const getCurriculum = async (id: string): Promise<Curriculum> => {
    const response = await fetch(`${API_URL}${id}`);
    if (!response.ok) {
        throw new Error('Failed to fetch curriculum');
    }
    return response.json();
};

export const createCurriculum = async (curriculum: CurriculumCreate): Promise<Curriculum> => {
    const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(curriculum),
    });
    if (!response.ok) {
        throw new Error('Failed to create curriculum');
    }
    return response.json();
};

export const getNode = async (curriculumId: string, nodeId: string): Promise<Node> => {
    const response = await fetch(`/api/v1/curriculums/${curriculumId}/nodes/${nodeId}`);
    if (!response.ok) {
        throw new Error('Failed to fetch node');
    }
    return response.json();
};

export const createNode = async (curriculumId: string, node: NodeCreate): Promise<Node> => {
    const response = await fetch(`/api/v1/curriculums/${curriculumId}/nodes`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(node),
    });
    if (!response.ok) {
        throw new Error('Failed to create node');
    }
    return response.json();
};

export const updateCurriculum = async (id: string, curriculum: CurriculumUpdate): Promise<Curriculum> => {
    const response = await fetch(`${API_URL}${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(curriculum),
    });
    if (!response.ok) {
        throw new Error('Failed to update curriculum');
    }
    return response.json();
};

export const deleteCurriculum = async (id: string): Promise<void> => {
    const response = await fetch(`${API_URL}${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        throw new Error('Failed to delete curriculum');
    }
};
