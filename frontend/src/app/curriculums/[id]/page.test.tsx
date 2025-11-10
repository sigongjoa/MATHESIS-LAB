import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import CurriculumDetailPage from './page';
import * as api from '@/lib/api';
import { MemoryRouterProvider } from 'next-router-mock/MemoryRouterProvider';
import { useNodesState, useEdgesState, addEdge } from 'reactflow'; // Import specific reactflow hooks

// Mock the API module
jest.mock('@/lib/api', () => ({
  __esModule: true,
  getCurriculumWithNodes: jest.fn(),
  reorderNode: jest.fn(),
  createNode: jest.fn(),
}));

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
    jest.clearAllMocks();
    (api.getCurriculumWithNodes as jest.Mock).mockReturnValue({
      curriculum: mockCurriculum,
      nodes: mockNodes,
    });
    // Mock useNodesState to return the mockNodes
    (useNodesState as jest.Mock).mockReturnValue([mockNodes, jest.fn(), jest.fn()]);
    (useEdgesState as jest.Mock).mockReturnValue([[], jest.fn(), jest.fn()]);
    (addEdge as jest.Mock).mockReturnValue([]);
  });

  test('fetches and displays curriculum details and nodes', async () => {
    (api.getCurriculumWithNodes as jest.Mock).mockResolvedValue({
      curriculum: mockCurriculum,
      nodes: mockNodes,
    });

    render(
      <MemoryRouterProvider url={`/curriculums/${mockCurriculumId}`}>
        <CurriculumDetailPage params={{ id: mockCurriculumId }} />
      </MemoryRouterProvider>
    );

    expect(screen.getByText(/Loading curriculum map.../i)).toBeInTheDocument();

    expect(await screen.findByText('Test Curriculum')).toBeInTheDocument();
    expect(await screen.findByText('A curriculum for testing')).toBeInTheDocument();
    expect(await screen.findByText('Node 1')).toBeInTheDocument();
    expect(await screen.findByText('Node 2')).toBeInTheDocument();
  });

  test('adds a new node when "Add Node" button is clicked', async () => {
    const newMockNode = {
      id: 'node-3',
      position: { x: 0, y: 0 },
      data: { node_id: 'node-3', title: 'New Node', description: 'New Description', parent_node_id: null, order_index: 2, curriculum_id: mockCurriculumId, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      type: 'custom',
    };

    (api.createNode as jest.Mock).mockResolvedValue(newMockNode.data); // Mock the API call for creating a node

    render(
      <MemoryRouterProvider url={`/curriculums/${mockCurriculumId}`}>
        <CurriculumDetailPage params={{ id: mockCurriculumId }} />
      </MemoryRouterProvider>
    );

    // Wait for initial data to load
    await screen.findByText('Test Curriculum');

    // Simulate clicking the "Add Node" button
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /Add Node/i }));
    });

    // Explicitly await the API call to ensure it has completed
    await api.createNode;

    // Assert that the API call was made
    expect(api.createNode).toHaveBeenCalledWith(mockCurriculumId, {
      title: 'New Node', // Default title for new node
      description: '',
      parent_node_id: null,
      order_index: 0, // Default order index
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
