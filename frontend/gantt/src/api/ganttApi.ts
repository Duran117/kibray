// =============================================================================
// Kibray Gantt - API Client
// =============================================================================

import { GanttData, GanttItem, GanttCategory, GanttDependency, GanttMode } from '../types/gantt';

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
   * Create a new schedule item
   */
  async createItem(item: Partial<GanttItem>): Promise<GanttItem> {
    const response = await fetch(`${this.baseUrl}/gantt/v2/items/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify(item),
    });

    return this.handleResponse<GanttItem>(response);
  }

  /**
   * Update an existing schedule item
   */
  async updateItem(itemId: number, updates: Partial<GanttItem>): Promise<GanttItem> {
    const response = await fetch(`${this.baseUrl}/gantt/v2/items/${itemId}/`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify(updates),
    });

    return this.handleResponse<GanttItem>(response);
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
    const response = await fetch(`${this.baseUrl}/schedule/categories/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify(category),
    });

    return this.handleResponse<GanttCategory>(response);
  }

  /**
   * Update category collapse state
   */
  async updateCategoryCollapse(categoryId: number, isCollapsed: boolean): Promise<void> {
    const response = await fetch(`${this.baseUrl}/schedule/categories/${categoryId}/`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      credentials: 'same-origin',
      body: JSON.stringify({ is_collapsed: isCollapsed }),
    });

    if (!response.ok) {
      throw new Error('Failed to update category');
    }
  }

  // ---------------------------------------------------------------------------
  // Dependencies CRUD
  // ---------------------------------------------------------------------------

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
        predecessor_id: predecessorId,
        successor_id: successorId,
        type,
        lag_days: lagDays,
      }),
    });

    return this.handleResponse<GanttDependency>(response);
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
        schedule_item_id: scheduleItemId,
        ...task,
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
