// =============================================================================
// Kibray Gantt - API Client
// =============================================================================

import { GanttData, GanttItem, GanttCategory, GanttDependency, GanttMode } from '../types/gantt';
import { toV2ItemPayload } from './adapters';

const DEFAULT_BASE_URL = '/api/v1';

/**
 * API Client for Gantt operations
 */
export class GanttApi {
  private baseUrl: string;
  private csrfToken: string;

  constructor(baseUrl: string = DEFAULT_BASE_URL, csrfToken: string = '') {
    this.baseUrl = baseUrl;
    this.csrfToken = csrfToken || this.getCsrfFromMeta();
  }

  /**
   * Get CSRF token from meta tag
   */
  private getCsrfFromMeta(): string {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') || '' : '';
  }

  /**
   * Default headers for requests
   */
  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
      'X-CSRFToken': this.csrfToken,
    };
  }

  /**
   * Handle response errors
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  // ---------------------------------------------------------------------------
  // Data Fetching
  // ---------------------------------------------------------------------------

  /**
   * Fetch gantt data based on mode
   */
  async fetchGanttData(mode: GanttMode, options: { projectId?: number; pmUserId?: number }): Promise<GanttData> {
    let url: string;

    switch (mode) {
      case 'project':
        if (!options.projectId) throw new Error('Project ID required for project mode');
        url = `${this.baseUrl}/gantt/v2/projects/${options.projectId}/`;
        break;
      case 'master':
        url = `${this.baseUrl}/schedule/master/`;
        break;
      case 'pm':
        url = `${this.baseUrl}/pm-calendar/api/data/`;
        break;
      case 'strategic':
        url = `${this.baseUrl}/strategic-planner/summary/`;
        break;
      default:
        throw new Error(`Unknown mode: ${mode}`);
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'same-origin',
    });

    return this.handleResponse<GanttData>(response);
  }

  // ---------------------------------------------------------------------------
  // Items CRUD
  // ---------------------------------------------------------------------------

  /**
   * Transform API item response to internal GanttItem format
   */
  private transformItemResponse(apiItem: any): GanttItem {
    return {
      id: apiItem.id,
      title: apiItem.name,
      description: apiItem.description || '',
      category_id: apiItem.phase,
      project_id: apiItem.project,
      start_date: apiItem.start_date,
      end_date: apiItem.end_date,
      status: this.mapStatusFromApi(apiItem.status),
      percent_complete: apiItem.progress || 0,
      weight_percent: parseFloat(apiItem.weight_percent) || 0,
      calculated_progress: apiItem.calculated_progress || 0,
      remaining_weight_percent: apiItem.remaining_weight_percent || 100,
      is_milestone: apiItem.is_milestone || false,
      is_personal: false,
      assigned_to: apiItem.assigned_to,
      assigned_to_name: apiItem.assigned_to_name,
      tasks: apiItem.tasks || [],
      order: apiItem.order || 0,
      notes: '',
      created_at: apiItem.created_at,
      updated_at: apiItem.updated_at,
    };
  }

  /**
   * Map API status to internal ItemStatus
   */
  private mapStatusFromApi(status: string): 'not_started' | 'in_progress' | 'completed' | 'done' | 'blocked' | 'on_hold' {
    const statusMap: Record<string, 'not_started' | 'in_progress' | 'completed' | 'done' | 'blocked' | 'on_hold'> = {
      'planned': 'not_started',
      'in_progress': 'in_progress',
      'done': 'done',
      'blocked': 'blocked',
    };
    return statusMap[status] || 'not_started';
  }

  /**
   * Create a new schedule item
   */
  async createItem(item: Partial<GanttItem>): Promise<GanttItem> {
    const payload = toV2ItemPayload(item);
    const response = await fetch(`${this.baseUrl}/gantt/v2/items/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    });

    const apiItem = await this.handleResponse<any>(response);
    return this.transformItemResponse(apiItem);
  }

  /**
   * Update an existing schedule item
   */
  async updateItem(itemId: number, updates: Partial<GanttItem>): Promise<GanttItem> {
    const payload = toV2ItemPayload(updates);
    const response = await fetch(`${this.baseUrl}/gantt/v2/items/${itemId}/`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    });

    const apiItem = await this.handleResponse<any>(response);
    return this.transformItemResponse(apiItem);
  }

  /**
   * Update item dates (optimized for drag/resize)
   */
  async updateItemDates(itemId: number, startDate: string, endDate: string): Promise<GanttItem> {
    return this.updateItem(itemId, {
      start_date: startDate,
      end_date: endDate,
    });
  }

  /**
   * Delete a schedule item
   */
  async deleteItem(itemId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/gantt/v2/items/${itemId}/`, {
      method: 'DELETE',
      headers: this.getHeaders(),
      credentials: 'same-origin',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
  }

  // ---------------------------------------------------------------------------
  // Categories CRUD
  // ---------------------------------------------------------------------------

  /**
   * Create a new category
   */
  async createCategory(category: Partial<GanttCategory>): Promise<GanttCategory> {
    const payload = {
      project: category.project_id,
      name: category.name,
      color: category.color,
      order: category.order,
      weight_percent: category.weight_percent,
      start_date: category.start_date,
      end_date: category.end_date,
    };

    const response = await fetch(`${this.baseUrl}/gantt/v2/phases/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    });

    const created = await this.handleResponse<any>(response);
    
    return {
      id: created.id,
      name: created.name,
      color: created.color,
      order: created.order,
      is_collapsed: false,
      project_id: created.project,
      start_date: created.start_date ?? null,
      end_date: created.end_date ?? null,
      weight_percent: created.weight_percent ?? 0,
      calculated_progress: created.calculated_progress ?? 0,
      remaining_weight_percent: created.remaining_weight_percent ?? 100,
    };
  }

  /**
   * Update an existing category
   */
  async updateCategory(categoryId: number, updates: Partial<GanttCategory>): Promise<GanttCategory> {
    const payload: any = {};
    if (updates.name !== undefined) payload.name = updates.name;
    if (updates.color !== undefined) payload.color = updates.color;
    if (updates.order !== undefined) payload.order = updates.order;
    if (updates.weight_percent !== undefined) payload.weight_percent = updates.weight_percent;
    if (updates.start_date !== undefined) payload.start_date = updates.start_date;
    if (updates.end_date !== undefined) payload.end_date = updates.end_date;

    const response = await fetch(`${this.baseUrl}/gantt/v2/phases/${categoryId}/`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    });

    const updated = await this.handleResponse<any>(response);
    return {
      id: updated.id,
      name: updated.name,
      color: updated.color,
      order: updated.order,
      is_collapsed: false,
      project_id: updated.project,
      start_date: updated.start_date ?? null,
      end_date: updated.end_date ?? null,
      weight_percent: updated.weight_percent ?? 0,
      calculated_progress: updated.calculated_progress ?? 0,
      remaining_weight_percent: updated.remaining_weight_percent ?? 100,
    };
  }

  /**
   * Delete a category
   */
  async deleteCategory(categoryId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/gantt/v2/phases/${categoryId}/`, {
      method: 'DELETE',
      headers: this.getHeaders(),
      credentials: 'same-origin',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
  }

  // ---------------------------------------------------------------------------
  // Dependencies CRUD
  // ---------------------------------------------------------------------------

  /**
   * Transform API dependency response to internal GanttDependency format
   */
  private transformDependencyResponse(apiDep: any): GanttDependency {
    return {
      id: apiDep.id,
      predecessor_id: apiDep.source_item,
      successor_id: apiDep.target_item,
      link_type: apiDep.dependency_type || 'FS',
      lag: 0,
    };
  }

  /**
   * Create a new dependency
   */
  async createDependency(
    predecessorId: number,
    successorId: number,
    type: 'FS' = 'FS',
    lagDays: number = 0
  ): Promise<GanttDependency> {
    const response = await fetch(`${this.baseUrl}/gantt/v2/dependencies/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify({
        source_item: predecessorId,
        target_item: successorId,
        dependency_type: type,
      }),
    });

    const apiDep = await this.handleResponse<any>(response);
    return this.transformDependencyResponse(apiDep);
  }

  /**
   * Delete a dependency
   */
  async deleteDependency(dependencyId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/gantt/v2/dependencies/${dependencyId}/`, {
      method: 'DELETE',
      headers: this.getHeaders(),
      credentials: 'same-origin',
    });

    if (!response.ok) {
      throw new Error('Failed to delete dependency');
    }
  }

  // ---------------------------------------------------------------------------
  // Tasks
  // ---------------------------------------------------------------------------

  /**
   * Create a task linked to a schedule item
   */
  async createTask(scheduleItemId: number, task: { title: string; assigned_to?: number }): Promise<void> {
    const response = await fetch(`${this.baseUrl}/gantt/v2/tasks/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify({
        item: scheduleItemId,  // Backend expects 'item' not 'schedule_item_id'
        title: task.title,
        assigned_to: task.assigned_to,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
  }
}

/**
 * Singleton instance
 */
let apiInstance: GanttApi | null = null;

/**
 * Get or create API instance
 */
export function getGanttApi(baseUrl?: string, csrfToken?: string): GanttApi {
  if (!apiInstance) {
    apiInstance = new GanttApi(baseUrl, csrfToken);
  }
  return apiInstance;
}

/**
 * Reset API instance (for testing)
 */
export function resetGanttApi(): void {
  apiInstance = null;
}
