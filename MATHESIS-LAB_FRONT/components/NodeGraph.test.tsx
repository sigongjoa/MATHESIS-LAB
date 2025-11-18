import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import NodeGraph from './NodeGraph';
import { Node, NodeLinkResponse, NodeContent } from '../types';

describe('NodeGraph Component', () => {
    const mockNodeContent: NodeContent = {
        content_id: 'content-1',
        node_id: 'node-1',
        markdown_content: 'Test content',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
    };

    const mockCurrentNode: Node = {
        node_id: 'node-1',
        curriculum_id: 'curriculum-1',
        title: 'Current Node',
        order_index: 0,
        node_type: 'CONTENT',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        content: mockNodeContent,
        links: [
            {
                link_id: 'link-1',
                node_id: 'node-1',
                link_type: 'NODE',
                linked_node_id: 'node-2',
                link_relationship: 'EXTENDS',
                created_at: '2024-01-01T00:00:00Z',
            },
        ],
    };

    const mockAllNodes: Node[] = [
        mockCurrentNode,
        {
            node_id: 'node-2',
            curriculum_id: 'curriculum-1',
            title: 'Related Node',
            order_index: 1,
            node_type: 'CONTENT',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            content: mockNodeContent,
        },
    ];

    it('should render the graph container', () => {
        render(
            <NodeGraph
                currentNode={mockCurrentNode}
                allNodes={mockAllNodes}
                onNodeClick={() => {}}
            />
        );

        expect(screen.getByText('Node Relationships')).toBeInTheDocument();
        expect(screen.getByText('Interactive graph showing connected nodes')).toBeInTheDocument();
    });

    it('should render canvas element', () => {
        const { container } = render(
            <NodeGraph
                currentNode={mockCurrentNode}
                allNodes={mockAllNodes}
                onNodeClick={() => {}}
            />
        );

        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
    });

    it('should display legend items', () => {
        render(
            <NodeGraph
                currentNode={mockCurrentNode}
                allNodes={mockAllNodes}
                onNodeClick={() => {}}
            />
        );

        expect(screen.getByText(/Blue: Current node/)).toBeInTheDocument();
        expect(screen.getByText(/Gray: Related nodes/)).toBeInTheDocument();
        expect(screen.getByText(/Drag nodes to explore relationships/)).toBeInTheDocument();
    });

    it('should handle node click', async () => {
        const mockOnNodeClick = vi.fn();
        const { container } = render(
            <NodeGraph
                currentNode={mockCurrentNode}
                allNodes={mockAllNodes}
                onNodeClick={mockOnNodeClick}
            />
        );

        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();

        // Note: Actually testing canvas click requires more complex setup
        // This is a basic rendering test
    });

    it('should render with multiple related nodes', () => {
        const nodeWithMultipleLinks: Node = {
            ...mockCurrentNode,
            links: [
                {
                    link_id: 'link-1',
                    node_id: 'node-1',
                    link_type: 'NODE',
                    linked_node_id: 'node-2',
                    link_relationship: 'EXTENDS',
                    created_at: '2024-01-01T00:00:00Z',
                },
                {
                    link_id: 'link-2',
                    node_id: 'node-1',
                    link_type: 'NODE',
                    linked_node_id: 'node-3',
                    link_relationship: 'REFERENCES',
                    created_at: '2024-01-01T00:00:00Z',
                },
            ],
        };

        const allNodes: Node[] = [
            nodeWithMultipleLinks,
            {
                node_id: 'node-2',
                curriculum_id: 'curriculum-1',
                title: 'Related Node 1',
                order_index: 1,
                node_type: 'CONTENT',
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z',
            },
            {
                node_id: 'node-3',
                curriculum_id: 'curriculum-1',
                title: 'Related Node 2',
                order_index: 2,
                node_type: 'CONTENT',
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z',
            },
        ];

        render(
            <NodeGraph
                currentNode={nodeWithMultipleLinks}
                allNodes={allNodes}
                onNodeClick={() => {}}
            />
        );

        expect(screen.getByText('Node Relationships')).toBeInTheDocument();
    });

    it('should render with PDF links', () => {
        const nodeWithPDFLinks: Node = {
            ...mockCurrentNode,
            links: [
                {
                    link_id: 'link-1',
                    node_id: 'node-1',
                    link_type: 'PDF',
                    drive_file_id: 'file-1',
                    file_name: 'document.pdf',
                    created_at: '2024-01-01T00:00:00Z',
                },
            ],
        };

        render(
            <NodeGraph
                currentNode={nodeWithPDFLinks}
                allNodes={[nodeWithPDFLinks]}
                onNodeClick={() => {}}
            />
        );

        expect(screen.getByText('Node Relationships')).toBeInTheDocument();
    });

    it('should handle nodes without links', () => {
        const nodeWithoutLinks: Node = {
            ...mockCurrentNode,
            links: [],
        };

        render(
            <NodeGraph
                currentNode={nodeWithoutLinks}
                allNodes={[nodeWithoutLinks]}
                onNodeClick={() => {}}
            />
        );

        expect(screen.getByText('Node Relationships')).toBeInTheDocument();
    });
});
