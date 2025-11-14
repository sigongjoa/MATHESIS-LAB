# Frontend Testing Strategy for MATHESIS LAB

This document outlines the strategy for testing the frontend application, focusing on the setup of the testing environment and the approach to writing unit and integration tests for key components and services.

## 1. Testing Framework Setup

### 1.1. Vitest Configuration

*   **Framework:** Vitest (chosen for its speed and seamless integration with Vite).
*   **Environment:** `jsdom` (simulates a browser environment for DOM testing).
*   **Globals:** `true` (allows using test utilities like `expect`, `describe`, `it` without explicit imports in every test file).
*   **Setup Files:** `./setupTests.ts` (for global test setup, e.g., extending `expect` matchers).

### 1.2. Dependencies

The following development dependencies are installed:

*   `vitest`: The core testing framework.
*   `@testing-library/react`: Utilities for testing React components in a user-centric way.
*   `@testing-library/jest-dom`: Provides custom Jest matchers for DOM elements, enhancing assertions.
*   `jsdom`: A JavaScript implementation of the W3C DOM and HTML standards, used as the test environment.

### 1.3. `package.json` Script

A `test` script is added to `package.json` to easily run tests:

```json
"scripts": {
  "test": "vitest"
}
```

## 2. Testing Principles

*   **User-Centric Testing:** Prioritize testing features from the user's perspective, ensuring that the UI behaves as expected when users interact with it.
*   **Isolation:** Unit tests should test individual units (functions, components) in isolation, mocking external dependencies.
*   **Integration:** Integration tests should verify the interaction between multiple units (e.g., a component and its service).
*   **Mocking:** Use mocking extensively for API calls and external modules to ensure tests are fast, reliable, and independent of external systems.

## 3. Test Cases for Node Link Deletion Feature

### 3.1. Unit Tests for `services/nodeService.ts`

**Objective:** Verify that `nodeService.ts` functions correctly interact with the backend API.

*   **`fetchNodeDetails(nodeId: string)`:**
    *   **Success:** Should call the correct API endpoint (`GET /api/v1/nodes/{nodeId}`) and return parsed node data.
    *   **Failure (Network Error):** Should throw an error if the network request fails.
    *   **Failure (API Error):** Should throw an error if the API returns a non-OK status (e.g., 404, 500).

*   **`deleteNodeLink(nodeId: string, linkId: string)`:**
    *   **Success:** Should call the correct API endpoint (`DELETE /api/v1/nodes/{nodeId}/links/{linkId}`) with the `DELETE` method and return successfully (void).
    *   **Failure (Network Error):** Should throw an error if the network request fails.
    *   **Failure (API Error - 404):** Should throw a specific "Node link not found" error if the API returns 404.
    *   **Failure (API Error - Other):** Should throw a generic error for other non-OK API responses.

*   **`createZoteroLink(nodeId: string, linkData: NodeLinkZoteroCreate)`:**
    *   **Success:** Should call the correct API endpoint (`POST /api/v1/nodes/{nodeId}/links/zotero`) with the `POST` method and `linkData` in the body, returning the created link.
    *   **Failure:** Similar error handling as above.

*   **`createYouTubeLink(nodeId: string, linkData: NodeLinkYouTubeCreate)`:**
    *   **Success:** Should call the correct API endpoint (`POST /api/v1/nodes/{nodeId}/links/youtube`) with the `POST` method and `linkData` in the body, returning the created link.
    *   **Failure:** Similar error handling as above.

*   **`fetchNodeLinks(nodeId: string)`:**
    *   **Success:** Should call the correct API endpoint (`GET /api/v1/nodes/{nodeId}/links`) and return a list of `NodeLinkResponse`.
    *   **Failure:** Similar error handling as above.

### 3.2. Integration Tests for `pages/NodeEditor.tsx`

**Objective:** Verify that the `NodeEditor` component correctly displays linked resources, handles deletion, and updates the UI.

*   **Initial Render (Loading State):**
    *   Should display a "Loading data..." message while fetching data.

*   **Initial Render (Error State):**
    *   Should display an "Error: Failed to load data." message if data fetching fails.

*   **Initial Render (Success State - No Links):**
    *   Should display node content and a "No linked resources." message if the node has no links.

*   **Initial Render (Success State - With Links):**
    *   Should display node content and a list of `LinkedResourceItem` components for each linked resource.
    *   Each `LinkedResourceItem` should display the correct title and icon.

*   **Delete Link - Confirmation Modal Display:**
    *   When the delete button of a `LinkedResourceItem` is clicked, the confirmation modal should appear.
    *   The modal should display the correct resource title.

*   **Delete Link - Cancel Action:**
    *   Clicking "Cancel" in the confirmation modal should close the modal and leave the linked resource list unchanged.

*   **Delete Link - Successful Deletion:**
    *   Clicking "Confirm Remove" in the modal should:
        *   Call `nodeService.deleteNodeLink` with the correct `nodeId` and `linkId`.
        *   Remove the deleted link from the displayed list.
        *   Close the confirmation modal.

*   **Delete Link - Deletion Failure:**
    *   If `nodeService.deleteNodeLink` throws an error, the modal should close, the link should remain in the list, and an error message should be displayed (e.g., a toast notification, though not implemented yet, so console error is fine for now).
