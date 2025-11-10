// frontend/jest.setup.tsx

import '@testing-library/jest-dom';
import React from 'react'; // React import is needed for JSX in the mock

// Mock next/navigation using next-router-mock and explicitly mock useParams
jest.mock("next/navigation", () => ({
  ...require("next-router-mock/navigation"),
  useParams: () => ({ id: 'test-curriculum-id' }), // Explicitly mock useParams
}));
