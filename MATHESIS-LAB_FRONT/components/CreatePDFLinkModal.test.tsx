import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import CreatePDFLinkModal from './CreatePDFLinkModal';
import * as nodeService from '../services/nodeService';

vi.mock('../services/nodeService');

const mockNodeId = 'test-node-id';
const mockOnClose = vi.fn();
const mockOnLinkCreated = vi.fn();

describe('CreatePDFLinkModal', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the modal with all form fields', () => {
        render(
            <CreatePDFLinkModal
                nodeId={mockNodeId}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        expect(screen.getByText('Link PDF File')).toBeInTheDocument();
        expect(screen.getByLabelText(/Google Drive File ID/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/File Name/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/File Size/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/MIME Type/i)).toBeInTheDocument();
    });

    it('shows error when required fields are missing', async () => {
        render(
            <CreatePDFLinkModal
                nodeId={mockNodeId}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        const submitButton = screen.getByText('Create Link');
        fireEvent.click(submitButton);

        expect(await screen.findByText(/Drive File ID and File Name are required/i)).toBeInTheDocument();
    });

    it('calls createPDFLink with correct data on form submission', async () => {
        const mockLink = {
            link_id: 'link-1',
            node_id: mockNodeId,
            link_type: 'DRIVE_PDF',
            drive_file_id: 'test-file-id',
            file_name: 'test.pdf',
            file_size_bytes: 2048576,
            file_mime_type: 'application/pdf',
            created_at: new Date().toISOString(),
        };

        (nodeService.createPDFLink as jest.Mock).mockResolvedValue(mockLink);

        const user = userEvent.setup();
        render(
            <CreatePDFLinkModal
                nodeId={mockNodeId}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        const fileIdInput = screen.getByPlaceholderText(/1BwxN3u7KxxXX/i);
        const fileNameInput = screen.getByPlaceholderText(/lecture-notes\.pdf/i);
        const fileSizeInput = screen.getByPlaceholderText(/2048576/i);

        await user.type(fileIdInput, 'test-file-id');
        await user.type(fileNameInput, 'test.pdf');
        await user.type(fileSizeInput, '2048576');

        const submitButton = screen.getByText('Create Link');
        await user.click(submitButton);

        await waitFor(() => {
            expect(nodeService.createPDFLink).toHaveBeenCalledWith(mockNodeId, {
                drive_file_id: 'test-file-id',
                file_name: 'test.pdf',
                file_size_bytes: 2048576,
                file_mime_type: undefined,
            });
        });

        expect(mockOnLinkCreated).toHaveBeenCalledWith(mockLink);
        expect(mockOnClose).toHaveBeenCalled();
    });

    it('closes modal when cancel button is clicked', async () => {
        const user = userEvent.setup();
        render(
            <CreatePDFLinkModal
                nodeId={mockNodeId}
                onClose={mockOnClose}
                onLinkCreated={mockOnLinkCreated}
            />
        );

        const cancelButton = screen.getByText('Cancel');
        await user.click(cancelButton);

        expect(mockOnClose).toHaveBeenCalled();
    });
});
