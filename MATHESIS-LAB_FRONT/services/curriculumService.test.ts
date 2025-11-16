import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as curriculumService from './curriculumService';
import { Curriculum, CurriculumCreate, CurriculumUpdate } from '../types';

describe('curriculumService', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  describe('getCurriculums', () => {
    it('should fetch all curriculums', async () => {
      const mockData: Curriculum[] = [
        {
          curriculum_id: '1',
          title: 'Curriculum 1',
          description: 'Description 1',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          nodes: [],
        },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await curriculumService.getCurriculums();

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/curriculums/');
    });

    it('should throw error on failed response', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
      });

      await expect(curriculumService.getCurriculums()).rejects.toThrow(
        'Failed to fetch curriculums'
      );
    });
  });

  describe('getCurriculum', () => {
    it('should fetch a single curriculum', async () => {
      const mockData: Curriculum = {
        curriculum_id: '1',
        title: 'Curriculum 1',
        description: 'Description 1',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        nodes: [],
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await curriculumService.getCurriculum('1');

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/curriculums/1');
    });

    it('should throw error on failed response', async () => {
        (global.fetch as any).mockResolvedValueOnce({
          ok: false,
        });
  
        await expect(curriculumService.getCurriculum('1')).rejects.toThrow(
          'Failed to fetch curriculum'
        );
      });
  });

  describe('createCurriculum', () => {
    it('should create a curriculum', async () => {
      const input: CurriculumCreate = { title: 'New Curriculum', description: 'Test' };
      const mockResponse: Curriculum = {
        curriculum_id: '123',
        title: input.title,
        description: input.description || '',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        nodes: [],
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await curriculumService.createCurriculum(input);

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/curriculums/',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(input),
        })
      );
    });

    it('should throw error on failed response', async () => {
        const input: CurriculumCreate = { title: 'New Curriculum', description: 'Test' };
        (global.fetch as any).mockResolvedValueOnce({
          ok: false,
        });
  
        await expect(curriculumService.createCurriculum(input)).rejects.toThrow(
          'Failed to create curriculum'
        );
      });
  });

  describe('updateCurriculum', () => {
    it('should update a curriculum', async () => {
        const input: CurriculumUpdate = { title: 'Updated Curriculum' };
        const mockResponse: Curriculum = {
            curriculum_id: '1',
            title: 'Updated Curriculum',
            description: 'Original Description',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-02T00:00:00Z',
            nodes: [],
        };

        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse,
        });

        const result = await curriculumService.updateCurriculum('1', input);

        expect(result).toEqual(mockResponse);
        expect(global.fetch).toHaveBeenCalledWith(
            '/api/v1/curriculums/1',
            expect.objectContaining({
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(input),
            })
        );
    });

    it('should throw an error on failed response', async () => {
        const input: CurriculumUpdate = { title: 'Updated Curriculum' };
        (global.fetch as any).mockResolvedValueOnce({ ok: false });

        await expect(curriculumService.updateCurriculum('1', input)).rejects.toThrow(
            'Failed to update curriculum'
        );
    });
  });

  describe('deleteCurriculum', () => {
    it('should delete a curriculum', async () => {
        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
        });

        await curriculumService.deleteCurriculum('1');

        expect(global.fetch).toHaveBeenCalledWith(
            '/api/v1/curriculums/1',
            expect.objectContaining({
                method: 'DELETE',
            })
        );
    });

    it('should throw an error on failed response', async () => {
        (global.fetch as any).mockResolvedValueOnce({ ok: false });

        await expect(curriculumService.deleteCurriculum('1')).rejects.toThrow(
            'Failed to delete curriculum'
        );
    });
  });
});