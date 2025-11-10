import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CurriculumsPage from './page';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api', () => ({
  getCurriculums: jest.fn(),
  createCurriculum: jest.fn(),
  deleteCurriculum: jest.fn(),
  updateCurriculum: jest.fn(),
}));

const mockCurriculums = [
  { curriculum_id: '1', title: 'Math 101', description: 'Basic Math', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { curriculum_id: '2', title: 'History 101', description: 'World History', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
];

describe('CurriculumsPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    (api.getCurriculums as jest.Mock).mockClear();
    (api.createCurriculum as jest.Mock).mockClear();
    (api.deleteCurriculum as jest.Mock).mockClear();
    window.confirm = jest.fn(() => true); // Mock window.confirm to always be true
  });

  test('fetches and displays curriculums on initial render', async () => {
    (api.getCurriculums as jest.Mock).mockResolvedValue(mockCurriculums);
    render(<CurriculumsPage />);

    expect(screen.getByText(/Loading curriculums.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Math 101')).toBeInTheDocument();
      expect(screen.getByText('History 101')).toBeInTheDocument();
    });
  });

  test('creates a new curriculum and refreshes the list', async () => {
    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce(mockCurriculums) // Initial fetch
      .mockResolvedValueOnce([...mockCurriculums, { curriculum_id: '3', title: 'New Course', description: 'A new course', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }]); // Fetch after create
    
    (api.createCurriculum as jest.Mock).mockResolvedValue({ curriculum_id: '3', title: 'New Course', description: 'A new course' });

    render(<CurriculumsPage />);

    // Wait for initial load
    await screen.findByText('Math 101');

    // Fill out and submit the form
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'New Course' } });
    fireEvent.change(screen.getByLabelText(/Description/i), { target: { value: 'A new course' } });
    fireEvent.click(screen.getByRole('button', { name: /Create/i }));

    // Check if createCurriculum was called
    await waitFor(() => {
      expect(api.createCurriculum).toHaveBeenCalledWith({ title: 'New Course', description: 'A new course' });
    });

    // Check if the new curriculum is displayed
    await waitFor(() => {
      expect(screen.getByText('New Course')).toBeInTheDocument();
    });
  });

  test('deletes a curriculum and refreshes the list', async () => {
    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce(mockCurriculums) // Initial fetch
      .mockResolvedValueOnce([mockCurriculums[1]]); // Fetch after delete

    (api.deleteCurriculum as jest.Mock).mockResolvedValue(null);

    render(<CurriculumsPage />);

    // Wait for initial load
    await screen.findByText('Math 101');

    // Find all delete buttons and click the first one
    const deleteButtons = screen.getAllByRole('button', { name: /Delete/i });
    fireEvent.click(deleteButtons[0]);

    // Check if deleteCurriculum was called
    await waitFor(() => {
      expect(api.deleteCurriculum).toHaveBeenCalledWith('1');
    });

    // Check that the deleted item is no longer in the document
    await waitFor(() => {
      expect(screen.queryByText('Math 101')).not.toBeInTheDocument();
    });
  });
});
