import axios from 'axios';
import { ScheduleTask, ScheduleCategory, TaskFormData } from './types';

const API_BASE = '/api';

// Get CSRF token from cookie
function getCsrfToken(): string {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [key, value] = cookie.trim().split('=');
    if (key === name) return value;
  }
  return '';
}

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add CSRF token to requests
api.interceptors.request.use((config) => {
  const token = getCsrfToken();
  if (token && config.method !== 'get') {
    config.headers['X-CSRFToken'] = token;
  }
  return config;
});

export const scheduleApi = {
  // Get all tasks for a project
  getTasks: async (projectId: number): Promise<ScheduleTask[]> => {
    const response = await api.get(`/schedule/items/?project=${projectId}`);
    return response.data;
  },

  // Get categories for a project
  getCategories: async (projectId: number): Promise<ScheduleCategory[]> => {
    const response = await api.get(`/schedule/categories/?project=${projectId}`);
    return response.data;
  },

  // Create new task
  createTask: async (projectId: number, data: TaskFormData): Promise<ScheduleTask> => {
    const response = await api.post(`/schedule/items/`, {
      ...data,
      project: projectId,
    });
    return response.data;
  },

  // Update task
  updateTask: async (taskId: string, data: Partial<TaskFormData>): Promise<ScheduleTask> => {
    const response = await api.patch(`/schedule/items/${taskId}/`, data);
    return response.data;
  },

  // Delete task
  deleteTask: async (taskId: string): Promise<void> => {
    await api.delete(`/schedule/items/${taskId}/`);
  },

  // Bulk update tasks (for drag and drop)
  bulkUpdateTasks: async (updates: Array<{ id: string; start: string; end: string }>): Promise<void> => {
    await api.post(`/schedule/items/bulk_update/`, { updates });
  },
};
