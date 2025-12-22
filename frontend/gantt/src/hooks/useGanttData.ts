// =============================================================================
// Kibray Gantt - useGanttData Hook
// =============================================================================

import { useState, useEffect, useCallback } from 'react';
import { 
  GanttData, 
  GanttItem, 
  GanttCategory, 
  GanttDependency,
  GanttMode,
  GanttPermissions 
} from '../types/gantt';
import { getGanttApi } from '../api/ganttApi';

interface UseGanttDataOptions {
  mode: GanttMode;
  projectId?: number;
  pmUserId?: number;
  apiBaseUrl?: string;
  csrfToken?: string;
}

interface UseGanttDataReturn {
  // Data
  data: GanttData | null;
  categories: GanttCategory[];
  items: GanttItem[];
  dependencies: GanttDependency[];
  permissions: GanttPermissions;
  
  // State
  isLoading: boolean;
  error: string | null;
  isSaving: boolean;
  
  // Actions
  refetch: () => Promise<void>;
  updateItem: (itemId: number, updates: Partial<GanttItem>) => Promise<void>;
  updateItemDates: (itemId: number, startDate: string, endDate: string) => Promise<void>;
  createItem: (item: Partial<GanttItem>) => Promise<GanttItem | null>;
  deleteItem: (itemId: number) => Promise<void>;
  createCategory: (category: Partial<GanttCategory>) => Promise<GanttCategory | null>;
  toggleCategoryCollapse: (categoryId: number) => void;
  createDependency: (predecessorId: number, successorId: number) => Promise<GanttDependency | null>;
  deleteDependency: (dependencyId: number) => Promise<void>;
}

const DEFAULT_PERMISSIONS: GanttPermissions = {
  can_view: true,
  can_create: false,
  can_edit: false,
  can_delete: false,
};

export function useGanttData(options: UseGanttDataOptions): UseGanttDataReturn {
  const { mode, projectId, pmUserId, apiBaseUrl, csrfToken } = options;
  
  const [data, setData] = useState<GanttData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  
  // Local state for optimistic updates
  const [localCategories, setLocalCategories] = useState<GanttCategory[]>([]);
  const [localItems, setLocalItems] = useState<GanttItem[]>([]);
  const [localDependencies, setLocalDependencies] = useState<GanttDependency[]>([]);
  
  const api = getGanttApi(apiBaseUrl, csrfToken);

  // Fetch data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await api.fetchGanttData(mode, { projectId, pmUserId });
      setData(result);
      setLocalCategories(result.categories);
      setLocalItems(result.items);
      setLocalDependencies(result.dependencies);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, [api, mode, projectId, pmUserId]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Update item (full update)
  const updateItem = useCallback(async (itemId: number, updates: Partial<GanttItem>) => {
    setIsSaving(true);
    
    // Optimistic update
    setLocalItems(prev => 
      prev.map(item => item.id === itemId ? { ...item, ...updates } : item)
    );
    
    try {
      const updated = await api.updateItem(itemId, updates);
      setLocalItems(prev => 
        prev.map(item => item.id === itemId ? updated : item)
      );
    } catch (err) {
      // Rollback on error
      await fetchData();
      throw err;
    } finally {
      setIsSaving(false);
    }
  }, [api, fetchData]);

  // Update item dates (optimized for drag/resize)
  const updateItemDates = useCallback(async (itemId: number, startDate: string, endDate: string) => {
    setIsSaving(true);
    
    // Optimistic update
    setLocalItems(prev => 
      prev.map(item => 
        item.id === itemId 
          ? { ...item, start_date: startDate, end_date: endDate } 
          : item
      )
    );
    
    try {
      await api.updateItemDates(itemId, startDate, endDate);
    } catch (err) {
      // Rollback on error
      await fetchData();
      throw err;
    } finally {
      setIsSaving(false);
    }
  }, [api, fetchData]);

  // Create item
  const createItem = useCallback(async (item: Partial<GanttItem>): Promise<GanttItem | null> => {
    setIsSaving(true);
    
    try {
      const created = await api.createItem(item);
      setLocalItems(prev => [...prev, created]);
      return created;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create item');
      return null;
    } finally {
      setIsSaving(false);
    }
  }, [api]);

  // Delete item
  const deleteItem = useCallback(async (itemId: number) => {
    setIsSaving(true);
    
    // Optimistic delete
    const previousItems = localItems;
    setLocalItems(prev => prev.filter(item => item.id !== itemId));
    
    try {
      await api.deleteItem(itemId);
    } catch (err) {
      // Rollback on error
      setLocalItems(previousItems);
      throw err;
    } finally {
      setIsSaving(false);
    }
  }, [api, localItems]);

  // Create category
  const createCategory = useCallback(async (category: Partial<GanttCategory>): Promise<GanttCategory | null> => {
    setIsSaving(true);
    
    try {
      const created = await api.createCategory(category);
      setLocalCategories(prev => [...prev, created]);
      return created;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create category');
      return null;
    } finally {
      setIsSaving(false);
    }
  }, [api]);

  // Toggle category collapse (local only, optional persist)
  const toggleCategoryCollapse = useCallback((categoryId: number) => {
    setLocalCategories(prev => 
      prev.map(cat => 
        cat.id === categoryId 
          ? { ...cat, is_collapsed: !cat.is_collapsed } 
          : cat
      )
    );
    
    // Optionally persist to backend
    const category = localCategories.find(c => c.id === categoryId);
    if (category) {
      api.updateCategoryCollapse(categoryId, !category.is_collapsed).catch(() => {
        // Silent fail for collapse state
      });
    }
  }, [api, localCategories]);

  // Create dependency
  const createDependency = useCallback(async (
    predecessorId: number, 
    successorId: number
  ): Promise<GanttDependency | null> => {
    setIsSaving(true);
    
    try {
      const created = await api.createDependency(predecessorId, successorId);
      setLocalDependencies(prev => [...prev, created]);
      return created;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create dependency');
      return null;
    } finally {
      setIsSaving(false);
    }
  }, [api]);

  // Delete dependency
  const deleteDependency = useCallback(async (dependencyId: number) => {
    setIsSaving(true);
    
    // Optimistic delete
    const previousDeps = localDependencies;
    setLocalDependencies(prev => prev.filter(dep => dep.id !== dependencyId));
    
    try {
      await api.deleteDependency(dependencyId);
    } catch (err) {
      // Rollback on error
      setLocalDependencies(previousDeps);
      throw err;
    } finally {
      setIsSaving(false);
    }
  }, [api, localDependencies]);

  return {
    data,
    categories: localCategories,
    items: localItems,
    dependencies: localDependencies,
    permissions: data?.permissions || DEFAULT_PERMISSIONS,
    isLoading,
    error,
    isSaving,
    refetch: fetchData,
    updateItem,
    updateItemDates,
    createItem,
    deleteItem,
    createCategory,
    toggleCategoryCollapse,
    createDependency,
    deleteDependency,
  };
}
