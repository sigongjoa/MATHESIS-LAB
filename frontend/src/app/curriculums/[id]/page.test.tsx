import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import CurriculumDetailPage from './page';

import { MemoryRouterProvider } from 'next-router-mock/MemoryRouterProvider';
import { useNodesState, useEdgesState, addEdge } from 'reactflow'; // Import specific reactflow hooks



// Now import the mocked api functions as a namespace
import * as api from '@/lib/api';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
  })),
  useParams: jest.fn(() => ({ id: 'test-curriculum-id' })),
  useSearchParams: jest.fn(() => ({
    get: jest.fn(),
  })),
  usePathname: jest.fn(() => '/curriculums/test-curriculum-id'),
  useServerInsertedHTML: jest.fn(),
}));

// Mock next/link locally
jest.mock('next/link', () => {
  return ({ children, href, ...props }) => {
    return React.createElement('a', { href, ...props }, children);
  };
});

// Mock reactflow components and hooks locally
jest.mock('reactflow', () => ({
  __esModule: true,
  ...jest.requireActual('reactflow'), // Use actual implementation for other exports
  default: ({ children }) => <div data-testid="reactflow-mock">{children}</div>,
  MiniMap: () => <div data-testid="minimap-mock" />,
  Controls: () => <div data-testid="controls-mock" />,
  Background: () => <div data-testid="background-mock" />,
  useNodesState: jest.fn(),
  useEdgesState: jest.fn(),
  addEdge: jest.fn(),
}));

const mockCurriculumId = 'test-curriculum-id';
const mockCurriculum = {
  curriculum_id: mockCurriculumId,
  title: 'Test Curriculum',
  description: 'A curriculum for testing',
  is_public: true, // Added is_public field
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};
const mockNodes = [
  {
    id: 'node-1',
    position: { x: 0, y: 0 },
    data: { node_id: 'node-1', title: 'Node 1', description: 'Desc 1', parent_node_id: null, order_index: 0, curriculum_id: mockCurriculumId, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    type: 'custom',
  },
  {
    id: 'node-2',
    position: { x: 200, y: 200 },
    data: { node_id: 'node-2', title: 'Node 2', description: 'Desc 2', parent_node_id: 'node-1', order_index: 0, curriculum_id: mockCurriculumId, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    type: 'custom',
  },
];

describe('CurriculumDetailPage', () => {
  beforeEach(() => {
    jest.clearAllMocks(); // Clear mocks before each test

    // Set mock implementations on the imported 'api' functions using jest.spyOn
    jest.spyOn(api, 'getCurriculumWithNodes').mockResolvedValue({
      curriculum: mockCurriculum,
      nodes: mockNodes,
    });
    jest.spyOn(api, 'createNode').mockResolvedValue({
      node_id: 'node-3',
      title: 'New Node',
      description: '',
      parent_node_id: null,
      order_index: 2,
      curriculum_id: mockCurriculumId,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }); // Assuming createNode returns the created node object
    jest.spyOn(api, 'reorderNode').mockResolvedValue(undefined); // Assuming reorderNode has no return value

    // Mock useNodesState to return the mockNodes
    (useNodesState as jest.Mock).mockReturnValue([mockNodes, jest.fn(), jest.fn()]);
    (useEdgesState as jest.Mock).mockReturnValue([[], jest.fn(), jest.fn()]);
    (addEdge as jest.Mock).mockReturnValue([]);
  });

  afterEach(() => {
    jest.clearAllMocks(); // Clear mocks after each test
  });

  test('fetches and displays curriculum details and nodes', async () => {
    render(
      <MemoryRouterProvider url={`/curriculums/${mockCurriculumId}`}>
        <CurriculumDetailPage params={{ id: mockCurriculumId }} />
      </MemoryRouterProvider>
    );

    // Initial loading state
    expect(screen.getByText(/Loading curriculum map.../i)).toBeInTheDocument();

    // After data loads
    expect(await screen.findByText('Test Curriculum')).toBeInTheDocument();
    expect(await screen.findByText('A curriculum for testing')).toBeInTheDocument();
    expect(await screen.findByText('Node 1')).toBeInTheDocument();
    expect(await screen.findByText('Node 2')).toBeInTheDocument();

    // Verify API call
    expect(api.getCurriculumWithNodes).toHaveBeenCalledWith(mockCurriculumId);
  });

  test('displays public status in the header', async () => {
    (api.getCurriculumWithNodes as jest.Mock).mockResolvedValue({
      curriculum: { ...mockCurriculum, is_public: true },
      nodes: mockNodes,
    });

    render(
      <MemoryRouterProvider url={`/curriculums/${mockCurriculumId}`}>
        <CurriculumDetailPage params={{ id: mockCurriculumId }} />
      </MemoryRouterProvider>
    );

    await screen.findByText('Test Curriculum');
    expect(screen.getByTitle('Public')).toBeInTheDocument();
    expect(screen.queryByTitle('Private')).not.toBeInTheDocument();

    // Test for private
    (api.getCurriculumWithNodes as jest.Mock).mockResolvedValue({
      curriculum: { ...mockCurriculum, is_public: false },
      nodes: mockNodes,
    });
    render(
      <MemoryRouterProvider url={`/curriculums/${mockCurriculumId}`}>
        <CurriculumDetailPage params={{ id: mockCurriculumId }} />
      </MemoryRouterProvider>
    );
    await screen.findByText('Test Curriculum');
    expect(screen.getByTitle('Private')).toBeInTheDocument();
    expect(screen.queryByTitle('Public')).not.toBeInTheDocument();
  });

  test('adds a new node when "Add Node" button is clicked', async () => {
    render(
      <MemoryRouterProvider url={`/curriculums/${mockCurriculumId}`}>
        <CurriculumDetailPage params={{ id: mockCurriculumId }} />
      </MemoryRouterProvider>
    );

    // Wait for initial data to load
    await screen.findByText('Test Curriculum');

    // Simulate clicking the "Add Node" button
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /Add Node/i }));
    });

    // Assert that the API call was made
    expect(api.createNode).toHaveBeenCalledWith(mockCurriculumId, {
      title: 'New Node', // Default title for new node
      description: '',
      parent_node_id: null,
      order_index: mockNodes.length, // use current nodes length for order_index
    });

    // Assert that the new node appears on the screen
    expect(await screen.findByText('New Node')).toBeInTheDocument();
  });

  test('displays error message if fetching fails', async () => {
    (api.getCurriculumWithNodes as jest.Mock).mockRejectedValue(new Error('Failed to fetch'));

    render(
      <MemoryRouterProvider url={`/curriculums/${mockCurriculumId}`}>
        <CurriculumDetailPage params={{ id: mockCurriculumId }} />
      </MemoryRouterProvider>
    );

    expect(await screen.findByText(/Error: Failed to fetch/i)).toBeInTheDocument();
  });

  test('displays "Curriculum not found" if no data is returned', async () => {
    (api.getCurriculumWithNodes as jest.Mock).mockResolvedValue({
      curriculum: null,
      nodes: [],
    });

    render(
      <MemoryRouterProvider url={`/curriculums/${mockCurriculumId}`}>
        <CurriculumDetailPage params={{ id: mockCurriculumId }} />
      </MemoryRouterProvider>
    );

    expect(await screen.findByText(/Curriculum not found./i)).toBeInTheDocument();
  });
});