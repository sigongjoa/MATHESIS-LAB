
import {
    Node,
    NodeLinkResponse,
    NodeLinkZoteroCreate,
    NodeLinkYouTubeCreate,
    NodeLinkPDFCreate,
    NodeLinkNodeCreate
} from '../types';

const API_BASE_URL = '/api/v1/nodes';

export const fetchNodeDetails = async (nodeId: string): Promise<Node> => {
    const response = await fetch(`${API_BASE_URL}/${nodeId}`);
    if (!response.ok) {
        throw new Error('Failed to fetch node details');
    }
    return response.json();
};

export const createZoteroLink = async (nodeId: string, linkData: NodeLinkZoteroCreate): Promise<NodeLinkResponse> => {
    const response = await fetch(`${API_BASE_URL}/${nodeId}/links/zotero`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(linkData),
    });
    if (!response.ok) {
        throw new Error('Failed to create Zotero link');
    }
    return response.json();
};

export const createYouTubeLink = async (nodeId: string, linkData: NodeLinkYouTubeCreate): Promise<NodeLinkResponse> => {
    const response = await fetch(`${API_BASE_URL}/${nodeId}/links/youtube`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(linkData),
    });
    if (!response.ok) {
        throw new Error('Failed to create YouTube link');
    }
    return response.json();
};

export const deleteNodeLink = async (nodeId: string, linkId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/${nodeId}/links/${linkId}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        // Check for 404 specifically if the backend sends it for "not found"
        if (response.status === 404) {
            throw new Error('Node link not found');
        }
        throw new Error('Failed to delete node link');
    }
};

export const fetchNodeLinks = async (nodeId: string): Promise<NodeLinkResponse[]> => {
    const response = await fetch(`${API_BASE_URL}/${nodeId}/links`);
    if (!response.ok) {
        throw new Error('Failed to fetch node links');
    }
    return response.json();
};

// PDF Link endpoints
export const createPDFLink = async (nodeId: string, linkData: NodeLinkPDFCreate): Promise<NodeLinkResponse> => {
    const response = await fetch(`${API_BASE_URL}/${nodeId}/links/pdf`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(linkData),
    });
    if (!response.ok) {
        throw new Error('Failed to create PDF link');
    }
    return response.json();
};

export const getPDFLinks = async (nodeId: string): Promise<NodeLinkResponse[]> => {
    const response = await fetch(`${API_BASE_URL}/${nodeId}/links/pdf`);
    if (!response.ok) {
        throw new Error('Failed to fetch PDF links');
    }
    return response.json();
};

// Node-to-Node Link endpoints
export const createNodeLink = async (nodeId: string, linkData: NodeLinkNodeCreate): Promise<NodeLinkResponse> => {
    const response = await fetch(`${API_BASE_URL}/${nodeId}/links/node`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(linkData),
    });
    if (!response.ok) {
        throw new Error('Failed to create node link');
    }
    return response.json();
};

export const getNodeToNodeLinks = async (nodeId: string): Promise<NodeLinkResponse[]> => {
    const response = await fetch(`${API_BASE_URL}/${nodeId}/links/node`);
    if (!response.ok) {
        throw new Error('Failed to fetch node-to-node links');
    }
    return response.json();
};
