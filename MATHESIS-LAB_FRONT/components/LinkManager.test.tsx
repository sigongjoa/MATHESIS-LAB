import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import LinkManager from './LinkManager';
import { NodeLinkResponse } from '../types';

const mockPDFLink: NodeLinkResponse = {
    link_id: 'pdf-link-1',
    node_id: 'node-1',
    link_type: 'DRIVE_PDF',
    drive_file_id: 'file-123',
    file_name: 'lecture-notes.pdf',
    file_size_bytes: 2048576,
    file_mime_type: 'application/pdf',
    created_at: '2024-01-01T00:00:00Z',
};

const mockNodeLink: NodeLinkResponse = {
    link_id: 'node-link-1',
    node_id: 'node-1',
    link_type: 'NODE',
    linked_node_id: 'node-2',
    link_relationship: 'EXTENDS',
    created_at: '2024-01-01T00:00:00Z',
};

const mockYouTubeLink: NodeLinkResponse = {
    link_id: 'yt-link-1',
    node_id: 'node-1',
    link_type: 'YOUTUBE',
    youtube_video_id: 'video-123',
    created_at: '2024-01-01T00:00:00Z',
};

const mockDeleteRequest = vi.fn();
const mockAddPDFClick = vi.fn();
const mockAddNodeLinkClick = vi.fn();

describe('LinkManager', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders empty state messages when no links exist', () => {
        render(
            <LinkManager
                links={[]}
                onDeleteRequest={mockDeleteRequest}
                onAddPDFClick={mockAddPDFClick}
                onAddNodeLinkClick={mockAddNodeLinkClick}
            />
        );

        expect(screen.getByText(/No PDF files linked yet/i)).toBeInTheDocument();
        expect(screen.getByText(/No node links yet/i)).toBeInTheDocument();
    });

    it('renders PDF links in PDF section', () => {
        render(
            <LinkManager
                links={[mockPDFLink]}
                onDeleteRequest={mockDeleteRequest}
                onAddPDFClick={mockAddPDFClick}
                onAddNodeLinkClick={mockAddNodeLinkClick}
            />
        );

        expect(screen.getByText('lecture-notes.pdf')).toBeInTheDocument();
        expect(screen.getByText(/2.00 MB/)).toBeInTheDocument();
    });

    it('renders node-to-node links in Node Links section', () => {
        render(
            <LinkManager
                links={[mockNodeLink]}
                onDeleteRequest={mockDeleteRequest}
                onAddPDFClick={mockAddPDFClick}
                onAddNodeLinkClick={mockAddNodeLinkClick}
            />
        );

        expect(screen.getByText(/Linked Node \(EXTENDS\)/)).toBeInTheDocument();
        expect(screen.getByText(/ID: node-2/)).toBeInTheDocument();
    });

    it('renders other resource types in Other Resources section', () => {
        render(
            <LinkManager
                links={[mockYouTubeLink]}
                onDeleteRequest={mockDeleteRequest}
                onAddPDFClick={mockAddPDFClick}
                onAddNodeLinkClick={mockAddNodeLinkClick}
            />
        );

        expect(screen.getByText(/Other Resources/)).toBeInTheDocument();
        expect(screen.getByText(/YouTube: video-123/)).toBeInTheDocument();
    });

    it('calls onAddPDFClick when PDF add button is clicked', () => {
        render(
            <LinkManager
                links={[]}
                onDeleteRequest={mockDeleteRequest}
                onAddPDFClick={mockAddPDFClick}
                onAddNodeLinkClick={mockAddNodeLinkClick}
            />
        );

        const addPDFButton = screen.getByRole('button', { name: /\+ Add PDF/i });
        fireEvent.click(addPDFButton);

        expect(mockAddPDFClick).toHaveBeenCalled();
    });

    it('calls onAddNodeLinkClick when Node Link add button is clicked', () => {
        render(
            <LinkManager
                links={[]}
                onDeleteRequest={mockDeleteRequest}
                onAddPDFClick={mockAddPDFClick}
                onAddNodeLinkClick={mockAddNodeLinkClick}
            />
        );

        const addNodeLinkButton = screen.getByRole('button', { name: /\+ Add Link/i });
        fireEvent.click(addNodeLinkButton);

        expect(mockAddNodeLinkClick).toHaveBeenCalled();
    });

    it('calls onDeleteRequest when delete button is clicked', () => {
        render(
            <LinkManager
                links={[mockPDFLink, mockNodeLink]}
                onDeleteRequest={mockDeleteRequest}
                onAddPDFClick={mockAddPDFClick}
                onAddNodeLinkClick={mockAddNodeLinkClick}
            />
        );

        const deleteButtons = screen.getAllByRole('button', { name: '' });
        // First delete button is for the PDF link
        fireEvent.click(deleteButtons[deleteButtons.length - 2]);

        expect(mockDeleteRequest).toHaveBeenCalledWith(mockPDFLink);
    });

    it('renders multiple links of different types correctly', () => {
        render(
            <LinkManager
                links={[mockPDFLink, mockNodeLink, mockYouTubeLink]}
                onDeleteRequest={mockDeleteRequest}
                onAddPDFClick={mockAddPDFClick}
                onAddNodeLinkClick={mockAddNodeLinkClick}
            />
        );

        // Check PDF section
        expect(screen.getByText('PDF Files')).toBeInTheDocument();
        expect(screen.getByText('lecture-notes.pdf')).toBeInTheDocument();

        // Check Node Links section
        expect(screen.getByText('Node Links')).toBeInTheDocument();
        expect(screen.getByText(/Linked Node \(EXTENDS\)/)).toBeInTheDocument();

        // Check Other Resources section
        expect(screen.getByText('Other Resources')).toBeInTheDocument();
        expect(screen.getByText(/YouTube: video-123/)).toBeInTheDocument();
    });

    it('handles links with missing optional fields gracefully', () => {
        const linkWithoutFileSize: NodeLinkResponse = {
            ...mockPDFLink,
            file_size_bytes: undefined,
        };

        render(
            <LinkManager
                links={[linkWithoutFileSize]}
                onDeleteRequest={mockDeleteRequest}
                onAddPDFClick={mockAddPDFClick}
                onAddNodeLinkClick={mockAddNodeLinkClick}
            />
        );

        expect(screen.getByText('lecture-notes.pdf')).toBeInTheDocument();
        expect(screen.getByText('PDF File')).toBeInTheDocument();
    });
});
