import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import CreateNodeLinkModal from './CreateNodeLinkModal';
import * as nodeService from '../services/nodeService';
import { Node } from '../types';

vi.mock('../services/nodeService');

const mockNodeId = 'test-node-id';
const mockCurriculumId = 'test-curriculum-id';
const mockOnClose = vi.fn();
const mockOnLinkCreated = vi.fn();

const mockAvailableNodes: Node[] = [
    {
        node_id: 'node-1',
        curriculum_id: mockCurriculumId,
        title: 'Introduction to Algebra',
        order_index: 1,
        node_type: 'TOPIC',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
    },
    {
        node_id: 'node-2',
        curriculum_id: mockCurriculumId,
        title: 'Linear Equations',
        order_index: 2,
        node_type: 'TOPIC',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
    },
];

describe('CreateNodeLinkModal', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the modal with node selector and relationship type dropdown', () => {
        render(
            <CreateNodeLinkModal
                nodeId={mockNodeId}
                curriculumId={mockCurriculumId}
                availableNodes={mockAvailableNodes}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        expect(screen.getByText('Link to Another Node')).toBeInTheDocument();
        expect(screen.getByLabelText(/Target Node/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Relationship Type/i)).toBeInTheDocument();
    });

    it('excludes current node from available options', () => {
        const currentNodeId = mockAvailableNodes[0].node_id;
        render(
            <CreateNodeLinkModal
                nodeId={currentNodeId}
                curriculumId={mockCurriculumId}
                availableNodes={mockAvailableNodes}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        const selectElement = screen.getByLabelText(/Target Node/i) as HTMLSelectElement;
        const options = Array.from(selectElement.options).map(o => o.value);

        // Current node should not be in options
        expect(options).not.toContain(currentNodeId);
        // Other nodes should be in options
        expect(options).toContain(mockAvailableNodes[1].node_id);
    });

    it('shows error when no target node is selected', async () => {
        render(
            <CreateNodeLinkModal
                nodeId={mockNodeId}
                curriculumId={mockCurriculumId}
                availableNodes={mockAvailableNodes}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        const submitButton = screen.getByText('Create Link');
        fireEvent.click(submitButton);

        expect(await screen.findByText(/Target Node is required/i)).toBeInTheDocument();
    });

    it('shows error when trying to link node to itself', async () => {
        const user = userEvent.setup();
        render(
            <CreateNodeLinkModal
                nodeId={mockNodeId}
                curriculumId={mockCurriculumId}
                availableNodes={[
                    ...mockAvailableNodes,
                    {
                        node_id: mockNodeId,
                        curriculum_id: mockCurriculumId,
                        title: 'Current Node',
                        order_index: 0,
                        node_type: 'TOPIC',
                        created_at: '2024-01-01T00:00:00Z',
                        updated_at: '2024-01-01T00:00:00Z',
                    },
                ]}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        const selectElement = screen.getByLabelText(/Target Node/i);
        await user.selectOptions(selectElement, mockNodeId);

        const submitButton = screen.getByText('Create Link');
        fireEvent.click(submitButton);

        expect(await screen.findByText(/Cannot link a node to itself/i)).toBeInTheDocument();
    });

    it('calls createNodeLink with correct data on form submission', async () => {
        const mockLink = {
            link_id: 'link-1',
            node_id: mockNodeId,
            link_type: 'NODE',
            linked_node_id: mockAvailableNodes[0].node_id,
            link_relationship: 'EXTENDS',
            created_at: new Date().toISOString(),
        };

        (nodeService.createNodeLink as jest.Mock).mockResolvedValue(mockLink);

        const user = userEvent.setup();
        render(
            <CreateNodeLinkModal
                nodeId={mockNodeId}
                curriculumId={mockCurriculumId}
                availableNodes={mockAvailableNodes}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        const nodeSelect = screen.getByLabelText(/Target Node/i);
        const relationshipSelect = screen.getByLabelText(/Relationship Type/i);

        await user.selectOptions(nodeSelect, mockAvailableNodes[0].node_id);
        await user.selectOptions(relationshipSelect, 'EXTENDS');

        const submitButton = screen.getByText('Create Link');
        await user.click(submitButton);

        await waitFor(() => {
            expect(nodeService.createNodeLink).toHaveBeenCalledWith(mockNodeId, {
                linked_node_id: mockAvailableNodes[0].node_id,
                link_relationship: 'EXTENDS',
            });
        });

        expect(mockOnLinkCreated).toHaveBeenCalledWith(mockLink);
        expect(mockOnClose).toHaveBeenCalled();
    });

    it('handles API errors gracefully', async () => {
        (nodeService.createNodeLink as jest.Mock).mockRejectedValue(new Error('API Error'));

        const user = userEvent.setup();
        render(
            <CreateNodeLinkModal
                nodeId={mockNodeId}
                curriculumId={mockCurriculumId}
                availableNodes={mockAvailableNodes}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        const nodeSelect = screen.getByLabelText(/Target Node/i);
        await user.selectOptions(nodeSelect, mockAvailableNodes[0].node_id);

        const submitButton = screen.getByText('Create Link');
        await user.click(submitButton);

        expect(await screen.findByText(/Failed to create node link/i)).toBeInTheDocument();
        expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('closes modal when cancel button is clicked', async () => {
        const user = userEvent.setup();
        render(
            <CreateNodeLinkModal
                nodeId={mockNodeId}
                curriculumId={mockCurriculumId}
                availableNodes={mockAvailableNodes}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        const cancelButton = screen.getByText('Cancel');
        await user.click(cancelButton);

        expect(mockOnClose).toHaveBeenCalled();
    });
});
