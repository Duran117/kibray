import axios from 'axios';
import { ScheduleTask, ScheduleCategory, TaskFormData } from './types';

const API_BASE = '/api/v1';

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
  withCredentials: true,
});

// Add CSRF token to requests
api.interceptors.request.use((config) => {
  const token = getCsrfToken();
  if (token && config.method !== 'get') {
    config.headers['X-CSRFToken'] = token;
  }
  return config;
});

// Map backend ScheduleItem serializer shape to frontend ScheduleTask shape
function mapItem(raw: any): ScheduleTask {
  return {
    id: String(raw.id),
    name: raw.name || raw.title || 'Untitled',
    start: raw.planned_start || '',
    end: raw.planned_end || '',
    progress: raw.percent_complete ?? 0,
    status: (raw.status || 'NOT_STARTED') as ScheduleTask['status'],
    dependencies: [],
    category: raw.category ?? undefined,
    is_milestone: !!raw.is_milestone,
    custom_class: '',
  };
}

export const scheduleApi = {
  // Get all tasks for a project
  getTasks: async (projectId: number): Promise<ScheduleTask[]> => {
    const response = await api.get(`/schedule/items/?project=${projectId}`);
    return Array.isArray(response.data) ? response.data.map(mapItem) : [];
  },

  // Get categories for a project
  getCategories: async (projectId: number): Promise<ScheduleCategory[]> => {
    const response = await api.get(`/schedule/categories/?project=${projectId}`);
    return response.data;
  },

  // Create new task
  createTask: async (projectId: number, data: TaskFormData): Promise<ScheduleTask> => {
    const payload = {
      project: projectId,
      name: data.name, // serializer maps 'name' -> title
      planned_start: data.start,
      planned_end: data.end,
      status: data.status,
      percent_complete: data.progress,
      category: data.category,
      is_milestone: data.is_milestone,
      description: data.description,
    };
    const response = await api.post(`/schedule/items/`, payload);
    return mapItem(response.data);
  },

  // Update task
  updateTask: async (taskId: string, data: Partial<TaskFormData | ScheduleTask>): Promise<ScheduleTask> => {
    const payload: any = {};
    if (data.start) payload.planned_start = data.start;
    if (data.end) payload.planned_end = data.end;
    if (data.progress !== undefined) payload.percent_complete = data.progress;
    if ((data as any).status) payload.status = (data as any).status;
    if ((data as any).name) payload.name = (data as any).name;
  // 'name' maps to title via serializer source
    if ((data as any).category !== undefined) payload.category = (data as any).category;
    if ((data as any).is_milestone !== undefined) payload.is_milestone = (data as any).is_milestone;
    if ((data as any).description !== undefined) payload.description = (data as any).description;
    const response = await api.patch(`/schedule/items/${taskId}/`, payload);
    return mapItem(response.data);
  },

  // Update task dates only (optimized for drag & drop)
  updateTaskDates: async (taskId: string, start: string, end: string): Promise<ScheduleTask> => {
    const payload = {
      planned_start: start,
      planned_end: end,
    };
    const response = await api.patch(`/schedule/items/${taskId}/`, payload);
    return mapItem(response.data);
  },

  // Update task progress only
  updateTaskProgress: async (taskId: string, progress: number): Promise<ScheduleTask> => {
    const payload = {
      percent_complete: progress,
    };
    const response = await api.patch(`/schedule/items/${taskId}/`, payload);
    return mapItem(response.data);
  },

  // Delete task
  deleteTask: async (taskId: string): Promise<void> => {
    await api.delete(`/schedule/items/${taskId}/`);
  },

  // Bulk update tasks (for drag and drop)
  bulkUpdateTasks: async (updates: Array<{ id: string; start: string; end: string }>): Promise<void> => {
    const transformed = updates.map(u => ({ id: u.id, planned_start: u.start, planned_end: u.end }));
    await api.post(`/schedule/items/bulk_update/`, { updates: transformed });
  },
};
