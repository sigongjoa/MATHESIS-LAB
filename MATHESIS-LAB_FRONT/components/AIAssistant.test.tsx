import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AIAssistant from './AIAssistant';
import gcpService from '../services/gcpService';

// Mock GCP Service
vi.mock('../services/gcpService', () => ({
    default: {
        summarizeContent: vi.fn(),
        extendContent: vi.fn(),
        generateManimGuidelines: vi.fn(),
    },
}));

// Mock Spinner component
vi.mock('./Spinner', () => ({
    default: () => <div data-testid="spinner">Loading...</div>,
}));

describe('AIAssistant Component', () => {
    const mockAIResponse = {
        result: 'This is the AI generated result',
        tokens_used: 150,
        processing_time_ms: 2500,
    };

    beforeEach(() => {
        vi.clearAllMocks();
        (gcpService.summarizeContent as any).mockResolvedValue(mockAIResponse);
        (gcpService.extendContent as any).mockResolvedValue(mockAIResponse);
        (gcpService.generateManimGuidelines as any).mockResolvedValue(mockAIResponse);
    });

    it('should render AI assistant component', () => {
        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={() => {}}
            />
        );

        expect(screen.getByText(/AI Assistant/i)).toBeInTheDocument();
        expect(screen.getByText(/Powered by Vertex AI/i)).toBeInTheDocument();
    });

    it('should display summarize, expand, and manim buttons', () => {
        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={() => {}}
            />
        );

        expect(screen.getByText(/Summarize/i)).toBeInTheDocument();
        expect(screen.getByText(/Expand/i)).toBeInTheDocument();
        expect(screen.getByText(/Manim Guide/i)).toBeInTheDocument();
    });

    it('should disable buttons when no content is provided', () => {
        render(
            <AIAssistant
                content=""
                nodeId="node-1"
                onUpdateContent={() => {}}
            />
        );

        const buttons = screen.getAllByRole('button');
        buttons.forEach((button) => {
            expect(button).toBeDisabled();
        });
    });

    it('should call summarizeContent when summarize button is clicked', async () => {
        const mockCallback = vi.fn();
        render(
            <AIAssistant
                content="This is a long text that needs to be summarized"
                nodeId="node-1"
                onUpdateContent={mockCallback}
            />
        );

        const summarizeButton = screen.getByText(/Summarize/i);
        await userEvent.click(summarizeButton);

        await waitFor(() => {
            expect(gcpService.summarizeContent).toHaveBeenCalledWith(
                'node-1',
                'This is a long text that needs to be summarized'
            );
        });

        await waitFor(() => {
            expect(mockCallback).toHaveBeenCalledWith(mockAIResponse.result);
        });
    });

    it('should call extendContent when expand button is clicked', async () => {
        const mockCallback = vi.fn();
        render(
            <AIAssistant
                content="Short content"
                nodeId="node-1"
                onUpdateContent={mockCallback}
            />
        );

        const expandButton = screen.getByText(/Expand/i);
        await userEvent.click(expandButton);

        await waitFor(() => {
            expect(gcpService.extendContent).toHaveBeenCalledWith('node-1', 'Short content');
        });

        await waitFor(() => {
            expect(mockCallback).toHaveBeenCalledWith(mockAIResponse.result);
        });
    });

    it('should show results after AI operation', async () => {
        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={() => {}}
            />
        );

        const summarizeButton = screen.getByText(/Summarize/i);
        await userEvent.click(summarizeButton);

        await waitFor(() => {
            expect(screen.getByText(/AI Results History/i)).toBeInTheDocument();
            expect(screen.getByText(/Summarized Content/i)).toBeInTheDocument();
        });
    });

    it('should display processing time and tokens used in results', async () => {
        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={() => {}}
            />
        );

        const summarizeButton = screen.getByText(/Summarize/i);
        await userEvent.click(summarizeButton);

        await waitFor(() => {
            expect(screen.getByText(/2\.5s/)).toBeInTheDocument();
            expect(screen.getByText(/150 tokens/)).toBeInTheDocument();
        });
    });

    it('should allow hiding and showing results', async () => {
        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={() => {}}
            />
        );

        const summarizeButton = screen.getByText(/Summarize/i);
        await userEvent.click(summarizeButton);

        await waitFor(() => {
            expect(screen.getByText(/AI Results History/i)).toBeInTheDocument();
        });

        // Results should be visible initially
        expect(screen.getByText(/This is the AI generated result/)).toBeVisible();

        // Click hide
        const toggleButton = screen.getByText(/▼ Hide/);
        await userEvent.click(toggleButton);

        // Results should be hidden
        expect(screen.queryByText(/This is the AI generated result/)).not.toBeVisible();

        // Click show
        const showButton = screen.getByText(/▶ Show/);
        await userEvent.click(showButton);

        // Results should be visible again
        expect(screen.getByText(/This is the AI generated result/)).toBeVisible();
    });

    it('should allow using a result from history', async () => {
        const mockCallback = vi.fn();
        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={mockCallback}
            />
        );

        const summarizeButton = screen.getByText(/Summarize/i);
        await userEvent.click(summarizeButton);

        await waitFor(() => {
            expect(screen.getByText(/Use This Result/i)).toBeInTheDocument();
        });

        const useButton = screen.getByText(/Use This Result/i);
        await userEvent.click(useButton);

        expect(mockCallback).toHaveBeenCalledWith(mockAIResponse.result);
    });

    it('should handle file upload for Manim guidelines', async () => {
        const mockCallback = vi.fn();
        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={mockCallback}
            />
        );

        // Create a mock file
        const mockFile = new File(['image data'], 'test.png', { type: 'image/png' });

        // Find the file input
        const fileInput = screen.getByRole('button', { name: /Manim Guide/i }).parentElement?.querySelector(
            'input[type="file"]'
        ) as HTMLInputElement;

        if (fileInput) {
            // Simulate file selection
            fireEvent.change(fileInput, { target: { files: [mockFile] } });

            await waitFor(() => {
                expect(gcpService.generateManimGuidelines).toHaveBeenCalledWith('node-1', mockFile);
            });
        }
    });

    it('should display error message on failure', async () => {
        const errorMessage = 'API Error occurred';
        (gcpService.summarizeContent as any).mockRejectedValue(new Error(errorMessage));

        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={() => {}}
            />
        );

        const summarizeButton = screen.getByText(/Summarize/i);
        await userEvent.click(summarizeButton);

        await waitFor(() => {
            expect(screen.getByText(errorMessage)).toBeInTheDocument();
        });
    });

    it('should show loading spinner during AI operation', async () => {
        (gcpService.summarizeContent as any).mockImplementation(
            () =>
                new Promise((resolve) =>
                    setTimeout(() => resolve(mockAIResponse), 1000)
                )
        );

        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={() => {}}
            />
        );

        const summarizeButton = screen.getByText(/Summarize/i);
        await userEvent.click(summarizeButton);

        // Spinner should appear while loading
        expect(screen.getByTestId('spinner')).toBeInTheDocument();

        await waitFor(() => {
            expect(screen.queryByTestId('spinner')).not.toBeInTheDocument();
        });
    });

    it('should maintain result history after multiple operations', async () => {
        const mockSummaryResponse = {
            result: 'Summary result',
            tokens_used: 100,
            processing_time_ms: 2000,
        };

        const mockExtendResponse = {
            result: 'Extended result',
            tokens_used: 200,
            processing_time_ms: 3000,
        };

        (gcpService.summarizeContent as any).mockResolvedValue(mockSummaryResponse);
        (gcpService.extendContent as any).mockResolvedValue(mockExtendResponse);

        render(
            <AIAssistant
                content="Test content"
                nodeId="node-1"
                onUpdateContent={() => {}}
            />
        );

        // Run summarize
        const summarizeButton = screen.getByText(/Summarize/i);
        await userEvent.click(summarizeButton);

        await waitFor(() => {
            expect(screen.getByText('Summary result')).toBeInTheDocument();
            expect(screen.getByText(/AI Results History \(1\)/i)).toBeInTheDocument();
        });

        // Run expand
        const expandButton = screen.getByText(/Expand/i);
        await userEvent.click(expandButton);

        await waitFor(() => {
            expect(screen.getByText('Extended result')).toBeInTheDocument();
            expect(screen.getByText(/AI Results History \(2\)/i)).toBeInTheDocument();
        });

        // Both results should be visible
        expect(screen.getByText('Summary result')).toBeInTheDocument();
        expect(screen.getByText('Extended result')).toBeInTheDocument();
    });
});
