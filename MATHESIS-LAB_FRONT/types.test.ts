import { describe, it, expect } from 'vitest';
import {
  Node,
  NodeContent,
  NodeLinkResponse,
  NodeLinkZoteroCreate,
  Curriculum
} from './types';

describe('Type Definitions', () => {
  describe('Node interface', () => {
    it('should have required properties', () => {
      const node: Node = {
        node_id: '123',
        curriculum_id: '456',
        title: 'Test Node',
        order_index: 0,
        node_type: 'CONTENT',  // [NEW]
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      expect(node.node_id).toBeDefined();
      expect(node.title).toBeDefined();
      expect(node.curriculum_id).toBeDefined();
      expect(node.node_type).toBeDefined();  // [NEW]
    });

    it('should support optional properties', () => {
      const node: Node = {
        node_id: '123',
        curriculum_id: '456',
        title: 'Test Node',
        order_index: 0,
        node_type: 'SECTION',  // [NEW]
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        content: {
          content_id: 'c1',
          node_id: '123',
          markdown_content: 'Test content',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        links: [] // NodeLinkResponse[]
      };

      expect(node.content).toBeDefined();
      expect(node.links).toBeDefined();
      expect(node.node_type).toBe('SECTION');  // [NEW]
    });
  });

  describe('NodeLinkZoteroCreate interface', () => {
    it('should have zotero_key property (not zotero_item_id)', () => {
      const linkData: NodeLinkZoteroCreate = {
        zotero_key: 'ABC123',
      };

      expect(linkData.zotero_key).toBeDefined();
      expect('zotero_item_id' in linkData).toBe(false);
    });
  });

  describe('NodeContent interface', () => {
    it('should have markdown_content property', () => {
      const content: NodeContent = {
        content_id: '1',
        node_id: '2',
        markdown_content: '## Title',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      expect(content.markdown_content).toBeDefined();
      expect(typeof content.markdown_content).toBe('string');
    });
  });
});