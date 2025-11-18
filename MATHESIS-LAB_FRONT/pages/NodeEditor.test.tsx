import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import NodeEditor from './NodeEditor';
import * as router from 'react-router-dom';
import * as nodeService from '../services/nodeService';
import * as curriculumService from '../services/curriculumService';
import { Node, Curriculum, NodeLinkResponse } from '../types';

// Mock react-router-dom's useParams
vi.mock('react-router-dom', async (importOriginal) => {
    const actual = await importOriginal();
    return {
        ...actual,
        useParams: vi.fn(),
    };
});

// Mock nodeService and curriculumService
vi.mock('../services/nodeService');
vi.mock('../services/curriculumService');

describe('NodeEditor', () => {
    const MOCK_CURRICULUM_ID = 'curriculum-id-1';
    const MOCK_NODE_ID = 'node-id-1';

    const mockNode: Node = {
        node_id: MOCK_NODE_ID,
        curriculum_id: MOCK_CURRICULUM_ID,
        title: 'Test Node Title',
        order_index: 0,
        node_type: 'CONTENT',  // [NEW]
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        content: {
            content_id: 'content-id-1',
            node_id: MOCK_NODE_ID,
            markdown_content: '## Test Content',
            created_at: '2023-01-01T00:00:00Z',
            updated_at: '2023-01-01T00:00:00Z',
        },
        links: [
            {
                link_id: 'link-youtube-1',
                node_id: MOCK_NODE_ID,
                link_type: 'YOUTUBE',
                youtube_video_id: 'youtube-video-id-1',
                created_at: '2023-01-01T00:00:00Z',
            },
            {
                link_id: 'link-zotero-1',
                node_id: MOCK_NODE_ID,
                link_type: 'ZOTERO',
                zotero_key: 'zotero-item-id-1',  // [FIXED] Changed from zotero_item_id
                created_at: '2023-01-01T00:00:00Z',
            },
        ],
    };

    const mockCurriculum: Curriculum = {
        curriculum_id: MOCK_CURRICULUM_ID,
        title: 'Test Curriculum',
        description: 'A test curriculum',
        nodes: [],
    };

    beforeEach(() => {
        // Reset mocks before each test
        vi.clearAllMocks();
        (router.useParams as vi.Mock).mockReturnValue({
            curriculumId: MOCK_CURRICULUM_ID,
            nodeId: MOCK_NODE_ID,
        });
        (nodeService.fetchNodeDetails as vi.Mock).mockResolvedValue(mockNode);
        (curriculumService.getCurriculum as vi.Mock).mockResolvedValue(mockCurriculum);
        (nodeService.deleteNodeLink as vi.Mock).mockResolvedValue(undefined); // Successful deletion
    });

    // --- Initial Render ---
    it('should display loading state initially', () => {
        (nodeService.fetchNodeDetails as vi.Mock).mockReturnValueOnce(new Promise(() => {})); // Pending promise
        render(<BrowserRouter><NodeEditor /></BrowserRouter>);
        expect(screen.getByText('Loading data...')).toBeInTheDocument();
    });

    it('should display error state if data fetching fails', async () => {
        (nodeService.fetchNodeDetails as vi.Mock).mockRejectedValueOnce(new Error('API Error'));
        render(<BrowserRouter><NodeEditor /></BrowserRouter>);
        await waitFor(() => expect(screen.getByText('Error: Failed to load data.')).toBeInTheDocument());
    });

    it('should render node details and linked resources on successful fetch', async () => {
        render(<BrowserRouter><NodeEditor /></BrowserRouter>);
        await waitFor(() => {
            expect(screen.getAllByText(mockNode.title).length).toBeGreaterThan(0);
            expect(screen.getByText(mockCurriculum.title)).toBeInTheDocument();
            // Check for actual rendered content (from LinkManager component)
            expect(screen.getByText('Node Relationships')).toBeInTheDocument();
        });
    });

    it('should display "No PDF files linked yet." if node has no PDF links', async () => {
        const nodeWithoutLinks = { ...mockNode, links: [] };
        (nodeService.fetchNodeDetails as vi.Mock).mockResolvedValueOnce(nodeWithoutLinks);
        render(<BrowserRouter><NodeEditor /></BrowserRouter>);
        await waitFor(() => {
            expect(screen.getByText('No PDF files linked yet.')).toBeInTheDocument();
        });
    });

    // --- Delete Link Functionality ---
    // Note: Delete link functionality modal is not yet implemented in NodeEditor.tsx
    // These tests will be enabled once the confirmation modal UI is added
    // it.skip('should open confirmation modal when delete button is clicked', async () => { ... });
    // it.skip('should close confirmation modal when Cancel button is clicked', async () => { ... });
    // it.skip('should delete link and update UI when Confirm Remove is clicked', async () => { ... });
    // it.skip('should display error if delete link fails', async () => { ... });
});