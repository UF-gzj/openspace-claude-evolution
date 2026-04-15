import apiClient from './client';
import type { ClaudeArtifactItem, ClaudeDraft, ClaudeLifecycleItem, ClaudeOverview } from './types';

export const claudeApi = {
  async getOverview(): Promise<ClaudeOverview> {
    const response = await apiClient.get<ClaudeOverview>('/claude/overview');
    return response.data;
  },

  async listArtifacts(): Promise<ClaudeArtifactItem[]> {
    const response = await apiClient.get<{ items: ClaudeArtifactItem[] }>('/claude/artifacts');
    return response.data.items;
  },

  async listDrafts(): Promise<ClaudeDraft[]> {
    const response = await apiClient.get<{ items: ClaudeDraft[] }>('/claude/drafts');
    return response.data.items;
  },

  async listLifecycle(): Promise<ClaudeLifecycleItem[]> {
    const response = await apiClient.get<{ items: ClaudeLifecycleItem[] }>('/claude/lifecycle');
    return response.data.items;
  },
};
