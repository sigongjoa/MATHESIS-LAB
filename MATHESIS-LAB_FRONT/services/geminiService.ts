
import { API_BASE_URL } from '../constants';

export const summarizeContent = async (nodeId: string): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/content/summarize`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to summarize content');
    }
    const data = await response.json();
    return data.summary;
};

export const extendContent = async (nodeId: string): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/content/extend`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to extend content');
    }
    const data = await response.json();
    return data.extension;
};
export const generateManimGuidelines = async (nodeId: string): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/content/manim`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate Manim guidelines');
    }
    const data = await response.json();
    return data.manim_guidelines;
};
