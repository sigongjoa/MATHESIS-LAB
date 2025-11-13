import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CurriculumsPage from './page';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api', () => ({
  getCurriculums: jest.fn(),
  getPublicCurriculums: jest.fn(), // Add this line
  createCurriculum: jest.fn(),
  deleteCurriculum: jest.fn(),
  updateCurriculum: jest.fn(),
}));

const mockCurriculums = [
  { curriculum_id: '1', title: 'Math 101', description: 'Basic Math', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { curriculum_id: '2', title: 'History 101', description: 'World History', is_public: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
];

describe('CurriculumsPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    (api.getCurriculums as jest.Mock).mockClear();
    (api.getPublicCurriculums as jest.Mock).mockClear();
    (api.createCurriculum as jest.Mock).mockClear();
    (api.deleteCurriculum as jest.Mock).mockClear();
    (api.updateCurriculum as jest.Mock).mockClear();
    window.confirm = jest.fn(() => true); // Mock window.confirm to always be true
  });

  test('fetches and displays all curriculums on initial render by default', async () => {
    (api.getCurriculums as jest.Mock).mockResolvedValue({ items: mockCurriculums, totalCount: mockCurriculums.length });
    render(<CurriculumsPage />);

    await waitFor(() => {
      expect(screen.getByText('Math 101')).toBeInTheDocument();
      expect(screen.getByText('History 101')).toBeInTheDocument();
      expect(screen.getByTitle('Public')).toBeInTheDocument();
      expect(screen.getByTitle('Private')).toBeInTheDocument();
    });
  });

  test('fetches and displays only public curriculums when toggle is active', async () => {
    (api.getCurriculums as jest.Mock).mockResolvedValue({ items: mockCurriculums, totalCount: mockCurriculums.length });
    (api.getPublicCurriculums as jest.Mock).mockResolvedValue({ items: [mockCurriculums[0]], totalCount: 1 }); // Only Math 101 is public
    render(<CurriculumsPage />);

    // Initial render shows all
    await waitFor(() => {
      expect(screen.getByText('Math 101')).toBeInTheDocument();
      expect(screen.getByText('History 101')).toBeInTheDocument();
    });

    // Click the toggle
    fireEvent.click(screen.getByRole('checkbox', { name: /Show Public Only:/i }));

    // Now it should show only public
    await waitFor(() => {
      expect(api.getPublicCurriculums).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Math 101')).toBeInTheDocument();
      expect(screen.queryByText('History 101')).not.toBeInTheDocument();
    });
  });

  test('creates a new curriculum and refreshes the list', async () => {
    const newCurriculum = { curriculum_id: '3', title: 'New Course', description: 'A new course', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce({ items: mockCurriculums, totalCount: mockCurriculums.length }) // Initial fetch
      .mockResolvedValueOnce({ items: [...mockCurriculums, newCurriculum], totalCount: mockCurriculums.length + 1 }); // Fetch after create
    
    (api.createCurriculum as jest.Mock).mockResolvedValue(newCurriculum);

    render(<CurriculumsPage />);

    // Wait for initial load
    await screen.findByText('Math 101');

    // Fill out and submit the form
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'New Course' } });
    fireEvent.change(screen.getByLabelText(/Description/i), { target: { value: 'A new course' } });
    fireEvent.click(screen.getByLabelText(/Public/i)); // Click the public checkbox
    fireEvent.click(screen.getByRole('button', { name: /Create/i }));

    // Check if createCurriculum was called
    await waitFor(() => {
      expect(api.createCurriculum).toHaveBeenCalledWith({ title: 'New Course', description: 'A new course', is_public: true });
    });

    // Check if the new curriculum is displayed
    await waitFor(() => {
      expect(screen.getByText('New Course')).toBeInTheDocument();
      expect(screen.getByTitle('Public')).toBeInTheDocument();
    });
  });

  test('deletes a curriculum and refreshes the list', async () => {
    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce({ items: mockCurriculums, totalCount: mockCurriculums.length }) // Initial fetch
      .mockResolvedValueOnce({ items: [mockCurriculums[1]], totalCount: 1 }); // Fetch after delete (Math 101 deleted)

    (api.deleteCurriculum as jest.Mock).mockResolvedValue(null);

    render(<CurriculumsPage />);

    // Wait for initial load
    await screen.findByText('Math 101');

    // Find all delete buttons and click the first one (Math 101)
    const deleteButtons = screen.getAllByRole('button', { name: /Delete/i });
    fireEvent.click(deleteButtons[0]);

    // Check if deleteCurriculum was called
    await waitFor(() => {
      expect(api.deleteCurriculum).toHaveBeenCalledWith('1');
    });

    // Check that the deleted item is no longer in the document
    await waitFor(() => {
      expect(screen.queryByText('Math 101')).not.toBeInTheDocument();
      expect(screen.getByText('History 101')).toBeInTheDocument(); // History 101 should still be there
    });
  });

  test('fetches curriculums with pagination parameters', async () => {
    const mockCurriculumsPage1 = [
      { curriculum_id: '1', title: 'Curriculum 1', description: 'Desc 1', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '2', title: 'Curriculum 2', description: 'Desc 2', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '3', title: 'Curriculum 3', description: 'Desc 3', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '4', title: 'Curriculum 4', description: 'Desc 4', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '5', title: 'Curriculum 5', description: 'Desc 5', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ];
    const mockCurriculumsPage2 = [
      { curriculum_id: '6', title: 'Curriculum 6', description: 'Desc 6', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '7', title: 'Curriculum 7', description: 'Desc 7', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ];
    const totalCount = mockCurriculumsPage1.length + mockCurriculumsPage2.length; // 7 items total

    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce({ items: mockCurriculumsPage1, totalCount: totalCount }) // First page
      .mockResolvedValueOnce({ items: mockCurriculumsPage2, totalCount: totalCount }); // Second page

    render(<CurriculumsPage />);

    // Initial fetch should be for skip=0, limit=5
    await waitFor(() => {
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 0, limit: 5 });
      expect(screen.getByText('Curriculum 1')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 6')).not.toBeInTheDocument();
    });

    // Click next page
    fireEvent.click(await screen.findByRole('button', { name: /Next/i }));

    // Second fetch should be for skip=5, limit=5
    await waitFor(() => {
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 5, limit: 5 });
      expect(screen.getByText('Curriculum 6')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 1')).not.toBeInTheDocument();
    });

    // Click previous page
    fireEvent.click(await screen.findByRole('button', { name: /Previous/i }));

    // Third fetch should be for skip=0, limit=5
    await waitFor(() => {
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 0, limit: 5 });
      expect(screen.getByText('Curriculum 1')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 6')).not.toBeInTheDocument();
    });
  });

  test('pagination buttons are disabled correctly', async () => {
    const mockCurriculumsSinglePage = [
      { curriculum_id: '1', title: 'Curriculum 1', description: 'Desc 1', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '2', title: 'Curriculum 2', description: 'Desc 2', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ];
    const mockCurriculumsMoreThanOnePage = Array.from({ length: 7 }).map((_, i) => ({
      curriculum_id: String(i + 1), title: `Curriculum ${i + 1}`, description: `Desc ${i + 1}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));

    // Test case 1: Single page, both buttons disabled
    (api.getCurriculums as jest.Mock).mockResolvedValueOnce({ items: mockCurriculumsSinglePage, totalCount: mockCurriculumsSinglePage.length });
    render(<CurriculumsPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Previous/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /Next/i })).toBeDisabled();
    });

    // Test case 2: Multiple pages, Next enabled on first page
    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce({ items: mockCurriculumsMoreThanOnePage.slice(0, 5), totalCount: mockCurriculumsMoreThanOnePage.length }) // Page 1
      .mockResolvedValueOnce({ items: mockCurriculumsMoreThanOnePage.slice(5, 7), totalCount: mockCurriculumsMoreThanOnePage.length }); // Page 2

    render(<CurriculumsPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Previous/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /Next/i })).not.toBeDisabled();
    });

    // Go to next page
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));

    // On last page, Previous enabled, Next disabled
    await waitFor(() => {
      expect(screen.getByText('Curriculum 6')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Previous/i })).not.toBeDisabled();
      expect(screen.getByRole('button', { name: /Next/i })).toBeDisabled();
    });
  });

  test('creating a curriculum resets to the first page', async () => {
    const mockCurriculumsPage1 = Array.from({ length: 5 }).map((_, i) => ({
      curriculum_id: String(i + 1), title: `Curriculum ${i + 1}`, description: `Desc ${i + 1}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));
    const mockCurriculumsPage2 = Array.from({ length: 2 }).map((_, i) => ({
      curriculum_id: String(i + 6), title: `Curriculum ${i + 6}`, description: `Desc ${i + 6}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));
    const newCurriculum = { curriculum_id: '8', title: 'New Curriculum', description: 'New Desc', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
    const totalCountBeforeCreate = mockCurriculumsPage1.length + mockCurriculumsPage2.length; // 7
    const totalCountAfterCreate = totalCountBeforeCreate + 1; // 8

    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce({ items: mockCurriculumsPage1, totalCount: totalCountBeforeCreate }) // Initial fetch (page 1)
      .mockResolvedValueOnce({ items: mockCurriculumsPage2, totalCount: totalCountBeforeCreate }) // Fetch for page 2
      .mockResolvedValueOnce({ items: [...mockCurriculumsPage1, newCurriculum].slice(0, 5), totalCount: totalCountAfterCreate }); // Fetch after create (back to page 1)

    (api.createCurriculum as jest.Mock).mockResolvedValue(newCurriculum);

    render(<CurriculumsPage />);

    await screen.findByText('Curriculum 1');
    fireEvent.click(screen.getByRole('button', { name: /Next/i })); // Go to page 2
    await screen.findByText('Curriculum 6');

    // Create a new curriculum
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'New Curriculum' } });
    fireEvent.click(screen.getByRole('button', { name: /Create/i }));

    // Should reset to page 1 and refetch
    await waitFor(() => {
      expect(api.createCurriculum).toHaveBeenCalledTimes(1);
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 0, limit: 5 }); // Should fetch page 1
      expect(screen.getByText('Curriculum 1')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 6')).not.toBeInTheDocument();
    });
  });

  test('deleting a curriculum resets to the first page', async () => {
    const mockCurriculumsPage1 = Array.from({ length: 5 }).map((_, i) => ({
      curriculum_id: String(i + 1), title: `Curriculum ${i + 1}`, description: `Desc ${i + 1}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));
    const mockCurriculumsPage2 = Array.from({ length: 2 }).map((_, i) => ({
      curriculum_id: String(i + 6), title: `Curriculum ${i + 6}`, description: `Desc ${i + 6}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));
    const totalCountBeforeDelete = mockCurriculumsPage1.length + mockCurriculumsPage2.length; // 7
    const totalCountAfterDelete = totalCountBeforeDelete - 1; // 6

    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce({ items: mockCurriculumsPage1, totalCount: totalCountBeforeDelete }) // Initial fetch (page 1)
      .mockResolvedValueOnce({ items: mockCurriculumsPage2, totalCount: totalCountBeforeDelete }) // Fetch for page 2
      .mockResolvedValueOnce({ items: mockCurriculumsPage1.slice(0, 4), totalCount: totalCountAfterDelete }); // Fetch after delete (back to page 1, one less item)

    (api.deleteCurriculum as jest.Mock).mockResolvedValue(null);

    render(<CurriculumsPage />);

    await screen.findByText('Curriculum 1');
    fireEvent.click(screen.getByRole('button', { name: /Next/i })); // Go to page 2
    await screen.findByText('Curriculum 6');

    // Delete a curriculum (e.g., Curriculum 6)
    const deleteButtons = screen.getAllByRole('button', { name: /Delete/i });
    fireEvent.click(deleteButtons[0]); // Click delete for Curriculum 6

    // Should reset to page 1 and refetch
    await waitFor(() => {
      expect(api.deleteCurriculum).toHaveBeenCalledWith('6');
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 0, limit: 5 }); // Should fetch page 1
      expect(screen.getByText('Curriculum 1')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 6')).not.toBeInTheDocument();
    });
  });

  test('fetches curriculums with pagination parameters', async () => {
    const mockCurriculumsPage1 = [
      { curriculum_id: '1', title: 'Curriculum 1', description: 'Desc 1', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '2', title: 'Curriculum 2', description: 'Desc 2', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '3', title: 'Curriculum 3', description: 'Desc 3', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '4', title: 'Curriculum 4', description: 'Desc 4', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '5', title: 'Curriculum 5', description: 'Desc 5', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ];
    const mockCurriculumsPage2 = [
      { curriculum_id: '6', title: 'Curriculum 6', description: 'Desc 6', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '7', title: 'Curriculum 7', description: 'Desc 7', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ];

    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce(mockCurriculumsPage1) // First page
      .mockResolvedValueOnce(mockCurriculumsPage2); // Second page

    render(<CurriculumsPage />);

    // Initial fetch should be for skip=0, limit=5
    await waitFor(() => {
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 0, limit: 5 });
      expect(screen.getByText('Curriculum 1')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 6')).not.toBeInTheDocument();
    });

    // Click next page
    fireEvent.click(await screen.findByRole('button', { name: /Next/i }));

    // Second fetch should be for skip=5, limit=5
    await waitFor(() => {
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 5, limit: 5 });
      expect(screen.getByText('Curriculum 6')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 1')).not.toBeInTheDocument();
    });

    // Click previous page
    fireEvent.click(await screen.findByRole('button', { name: /Previous/i }));

    // Third fetch should be for skip=0, limit=5
    await waitFor(() => {
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 0, limit: 5 });
      expect(screen.getByText('Curriculum 1')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 6')).not.toBeInTheDocument();
    });
  });

  test('pagination buttons are disabled correctly', async () => {
    const mockCurriculumsSinglePage = [
      { curriculum_id: '1', title: 'Curriculum 1', description: 'Desc 1', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { curriculum_id: '2', title: 'Curriculum 2', description: 'Desc 2', is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ];

    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce(mockCurriculumsSinglePage) // First page
      .mockResolvedValueOnce([]); // Simulate no more items for next page

    render(<CurriculumsPage />);

    // On first page, Previous should be disabled, Next should be enabled (if more items are expected)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Previous/i })).toBeDisabled();
      // Since totalItems is based on data.length, and mockCurriculumsSinglePage.length is 2 (less than ITEMS_PER_PAGE=5),
      // totalPages will be 1, so Next button will also be disabled.
      expect(screen.getByRole('button', { name: /Next/i })).toBeDisabled();
    });

    // To properly test Next button enabled, we need more items than ITEMS_PER_PAGE
    const mockCurriculumsMoreThanOnePage = Array.from({ length: 7 }).map((_, i) => ({
      curriculum_id: String(i + 1), title: `Curriculum ${i + 1}`, description: `Desc ${i + 1}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));

    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce(mockCurriculumsMoreThanOnePage.slice(0, 5)) // Page 1
      .mockResolvedValueOnce(mockCurriculumsMoreThanOnePage.slice(5, 7)) // Page 2
      .mockResolvedValueOnce([]); // Page 3 (empty)

    render(<CurriculumsPage />);

    // On first page (with more items), Previous should be disabled, Next should be enabled
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Previous/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /Next/i })).not.toBeDisabled();
    });

    // Go to next page
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));

    // On second page, both should be enabled (if there's a third page, or Next disabled if it's the last)
    await waitFor(() => {
      expect(screen.getByText('Curriculum 6')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Previous/i })).not.toBeDisabled();
      // Since the mock for page 3 is empty, totalPages will be 2, so Next should be disabled
      expect(screen.getByRole('button', { name: /Next/i })).toBeDisabled();
    });
  });

  test('creating a curriculum resets to the first page', async () => {
    const mockCurriculumsPage1 = Array.from({ length: 5 }).map((_, i) => ({
      curriculum_id: String(i + 1), title: `Curriculum ${i + 1}`, description: `Desc ${i + 1}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));
    const mockCurriculumsPage2 = Array.from({ length: 2 }).map((_, i) => ({
      curriculum_id: String(i + 6), title: `Curriculum ${i + 6}`, description: `Desc ${i + 6}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));
    const mockCurriculumsAfterCreate = Array.from({ length: 6 }).map((_, i) => ({
      curriculum_id: String(i + 1), title: `Curriculum ${i + 1}`, description: `Desc ${i + 1}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));

    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce(mockCurriculumsPage1) // Initial fetch (page 1)
      .mockResolvedValueOnce(mockCurriculumsPage2) // Fetch for page 2
      .mockResolvedValueOnce(mockCurriculumsAfterCreate.slice(0, 5)); // Fetch after create (back to page 1)

    (api.createCurriculum as jest.Mock).mockResolvedValue({ curriculum_id: '8', title: 'New Curriculum', description: 'New Desc', is_public: true });

    render(<CurriculumsPage />);

    await screen.findByText('Curriculum 1');
    fireEvent.click(screen.getByRole('button', { name: /Next/i })); // Go to page 2
    await screen.findByText('Curriculum 6');

    // Create a new curriculum
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'New Curriculum' } });
    fireEvent.click(screen.getByRole('button', { name: /Create/i }));

    // Should reset to page 1 and refetch
    await waitFor(() => {
      expect(api.createCurriculum).toHaveBeenCalledTimes(1);
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 0, limit: 5 }); // Should fetch page 1
      expect(screen.getByText('Curriculum 1')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 6')).not.toBeInTheDocument();
    });
  });

  test('deleting a curriculum resets to the first page', async () => {
    const mockCurriculumsPage1 = Array.from({ length: 5 }).map((_, i) => ({
      curriculum_id: String(i + 1), title: `Curriculum ${i + 1}`, description: `Desc ${i + 1}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));
    const mockCurriculumsPage2 = Array.from({ length: 2 }).map((_, i) => ({
      curriculum_id: String(i + 6), title: `Curriculum ${i + 6}`, description: `Desc ${i + 6}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));
    const mockCurriculumsAfterDelete = Array.from({ length: 6 }).map((_, i) => ({
      curriculum_id: String(i + 1), title: `Curriculum ${i + 1}`, description: `Desc ${i + 1}`, is_public: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString()
    }));

    (api.getCurriculums as jest.Mock)
      .mockResolvedValueOnce(mockCurriculumsPage1) // Initial fetch (page 1)
      .mockResolvedValueOnce(mockCurriculumsPage2) // Fetch for page 2
      .mockResolvedValueOnce(mockCurriculumsAfterDelete.slice(0, 5)); // Fetch after delete (back to page 1)

    (api.deleteCurriculum as jest.Mock).mockResolvedValue(null);

    render(<CurriculumsPage />);

    await screen.findByText('Curriculum 1');
    fireEvent.click(screen.getByRole('button', { name: /Next/i })); // Go to page 2
    await screen.findByText('Curriculum 6');

    // Delete a curriculum (e.g., Curriculum 6)
    const deleteButtons = screen.getAllByRole('button', { name: /Delete/i });
    fireEvent.click(deleteButtons[0]); // Click delete for Curriculum 6

    // Should reset to page 1 and refetch
    await waitFor(() => {
      expect(api.deleteCurriculum).toHaveBeenCalledWith('6');
      expect(api.getCurriculums).toHaveBeenCalledWith({ skip: 0, limit: 5 }); // Should fetch page 1
      expect(screen.getByText('Curriculum 1')).toBeInTheDocument();
      expect(screen.queryByText('Curriculum 6')).not.toBeInTheDocument();
    });
  });
});
