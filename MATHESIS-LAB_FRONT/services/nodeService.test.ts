import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
    fetchNodeDetails,
    createZoteroLink,
    createYouTubeLink,
    deleteNodeLink,
    fetchNodeLinks,
} from './nodeService';
import { Node, NodeLinkResponse, NodeLinkZoteroCreate, NodeLinkYouTubeCreate } from '../types';

// Mock the global fetch API
const mockFetch = vi.fn();
global.fetch = mockFetch;

beforeEach(() => {
    mockFetch.mockClear();
});

describe('nodeService', () => {
    const MOCK_NODE_ID = 'node-id-123';
    const MOCK_LINK_ID = 'link-id-456';
    const MOCK_CURRICULUM_ID = 'curriculum-id-789'; // Not directly used in nodeService, but good for context

    // --- fetchNodeDetails ---
    describe('fetchNodeDetails', () => {
        it('should fetch node details successfully', async () => {
            const mockNode: Node = {
                node_id: MOCK_NODE_ID,
                curriculum_id: MOCK_CURRICULUM_ID,
                title: 'Test Node',
                order_index: 0,
                node_type: 'CONTENT',
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z',
                links: [],
            };
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockNode),
            });

            const result = await fetchNodeDetails(MOCK_NODE_ID);
            expect(result).toEqual(mockNode);
            expect(mockFetch).toHaveBeenCalledWith(`/api/v1/nodes/${MOCK_NODE_ID}`);
        });

        it('should throw an error if fetching node details fails', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 404,
                statusText: 'Not Found',
            });

            await expect(fetchNodeDetails(MOCK_NODE_ID)).rejects.toThrow('Failed to fetch node details');
        });
    });

    // --- deleteNodeLink ---
    describe('deleteNodeLink', () => {
        it('should delete a node link successfully', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                status: 204,
            });

            await deleteNodeLink(MOCK_NODE_ID, MOCK_LINK_ID);
            expect(mockFetch).toHaveBeenCalledWith(`/api/v1/nodes/${MOCK_NODE_ID}/links/${MOCK_LINK_ID}`, {
                method: 'DELETE',
            });
        });

        it('should throw "Node link not found" error if API returns 404', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 404,
                statusText: 'Not Found',
            });

            await expect(deleteNodeLink(MOCK_NODE_ID, MOCK_LINK_ID)).rejects.toThrow('Node link not found');
        });

        it('should throw a generic error if deleting node link fails with other status', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: 'Internal Server Error',
            });

            await expect(deleteNodeLink(MOCK_NODE_ID, MOCK_LINK_ID)).rejects.toThrow('Failed to delete node link');
        });
    });

    // --- createZoteroLink ---
    describe('createZoteroLink', () => {
        const mockLinkCreate: NodeLinkZoteroCreate = { zotero_key: 'zotero-item-789' };
        const mockLinkResponse: NodeLinkResponse = {
            link_id: MOCK_LINK_ID,
            node_id: MOCK_NODE_ID,
            link_type: 'ZOTERO',
            zotero_key: mockLinkCreate.zotero_key,
            created_at: '2023-01-01T00:00:00Z',
        };

        it('should create a Zotero link successfully', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockLinkResponse),
            });

            const result = await createZoteroLink(MOCK_NODE_ID, mockLinkCreate);
            expect(result).toEqual(mockLinkResponse);
            expect(mockFetch).toHaveBeenCalledWith(`/api/v1/nodes/${MOCK_NODE_ID}/links/zotero`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(mockLinkCreate),
            });
        });

        it('should throw an error if creating Zotero link fails', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
            });

            await expect(createZoteroLink(MOCK_NODE_ID, mockLinkCreate)).rejects.toThrow('Failed to create Zotero link');
        });
    });

    // --- createYouTubeLink ---
    describe('createYouTubeLink', () => {
        const mockLinkCreate: NodeLinkYouTubeCreate = { youtube_url: 'https://youtube.com/watch?v=test' };
        const mockLinkResponse: NodeLinkResponse = {
            link_id: MOCK_LINK_ID,
            node_id: MOCK_NODE_ID,
            link_type: 'YOUTUBE',
            youtube_video_id: 'test',
            created_at: '2023-01-01T00:00:00Z',
        };

        it('should create a YouTube link successfully', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockLinkResponse),
            });

            const result = await createYouTubeLink(MOCK_NODE_ID, mockLinkCreate);
            expect(result).toEqual(mockLinkResponse);
            expect(mockFetch).toHaveBeenCalledWith(`/api/v1/nodes/${MOCK_NODE_ID}/links/youtube`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(mockLinkCreate),
            });
        });

        it('should throw an error if creating YouTube link fails', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
            });

            await expect(createYouTubeLink(MOCK_NODE_ID, mockLinkCreate)).rejects.toThrow('Failed to create YouTube link');
        });
    });

    // --- fetchNodeLinks ---
    describe('fetchNodeLinks', () => {
        it('should fetch node links successfully', async () => {
            const mockLinks: NodeLinkResponse[] = [
                {
                    link_id: 'link-1',
                    node_id: MOCK_NODE_ID,
                    link_type: 'YOUTUBE',
                    youtube_video_id: 'video-1',
                    created_at: '2023-01-01T00:00:00Z',
                },
                {
                    link_id: 'link-2',
                    node_id: MOCK_NODE_ID,
                    link_type: 'ZOTERO',
                    zotero_key: 'zotero-1',
                    created_at: '2023-01-01T00:00:00Z',
                },
            ];
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockLinks),
            });

            const result = await fetchNodeLinks(MOCK_NODE_ID);
            expect(result).toEqual(mockLinks);
            expect(mockFetch).toHaveBeenCalledWith(`/api/v1/nodes/${MOCK_NODE_ID}/links`);
        });

        it('should throw an error if fetching node links fails', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: 'Internal Server Error',
            });

            await expect(fetchNodeLinks(MOCK_NODE_ID)).rejects.toThrow('Failed to fetch node links');
        });
    });
});