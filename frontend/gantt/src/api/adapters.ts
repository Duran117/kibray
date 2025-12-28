// =============================================================================
// Kibray Gantt - Data Adapters
// Transform backend API responses to internal Gantt types
// =============================================================================

import { GanttItem, GanttCategory, GanttDependency, GanttData, ItemStatus, GanttTask } from '../types/gantt';

/**
 * Transform V2 API response to internal GanttData format
 */
export function transformV2Response(apiResponse: any): GanttData {
  const { project, phases, dependencies, metadata } = apiResponse;

  // Transform phases to categories (with weight/progress info)
  const categories: GanttCategory[] = (phases || []).map((phase: any) => ({
    id: phase.id,
    name: phase.name,
    color: phase.color || '#1F2937', // Dark color for stages
    order: phase.order || 0,
    is_collapsed: false,
    project_id: phase.project,
    start_date: phase.start_date || null,
    end_date: phase.end_date || null,
    weight_percent: phase.weight_percent || 0,
    calculated_progress: phase.calculated_progress || 0,
    remaining_weight_percent: phase.remaining_weight_percent || 100,
  }));

  // Transform items from phases (with weight/progress info)
  const items: GanttItem[] = [];
  (phases || []).forEach((phase: any) => {
    (phase.items || []).forEach((item: any) => {
      items.push(transformItemV2(item, phase.id));
    });
  });

  // Transform dependencies
  const deps: GanttDependency[] = (dependencies || []).map((dep: any) => ({
    id: dep.id,
    predecessor_id: dep.source_item,
    successor_id: dep.target_item,
    link_type: mapDependencyType(dep.dependency_type),
    lag: 0,
  }));

  return {
    project: project ? {
      id: project.id,
      name: project.name,
      start_date: project.start_date,
      end_date: project.end_date,
      color: '#6366f1',
    } : undefined,
    categories,
    items,
    dependencies: deps,
    permissions: {
      can_view: true,
      can_create: true,
      can_edit: true,
      can_delete: true,
    },
    metadata: {
      ...metadata,
      project_progress: metadata?.project_progress || 0,
      total_stage_weight: metadata?.total_stage_weight || 0,
    },
  };
}

/**
 * Transform a single V2 item to GanttItem format
 */
function transformItemV2(item: any, phaseId: number): GanttItem {
  return {
    id: item.id,
    title: item.name,
    description: item.description || '',
    category_id: phaseId,
    project_id: item.project,
    start_date: item.start_date,
    end_date: item.end_date,
    status: mapStatusV2(item.status),
    percent_complete: item.calculated_progress || item.progress || 0,
    weight_percent: item.weight_percent || 0,
    calculated_progress: item.calculated_progress || 0,
    remaining_weight_percent: item.remaining_weight_percent || 100,
    is_milestone: item.is_milestone || false,
    is_personal: false,
    assigned_to: item.assigned_to,
    assigned_to_name: item.assigned_to_name,
    tasks: (item.tasks || []).map(transformTaskV2),
    order: item.order || 0,
    notes: '',
    created_at: item.created_at,
    updated_at: item.updated_at,
  };
}

/**
 * Transform a V2 task to GanttTask format
 */
function transformTaskV2(task: any): GanttTask {
  return {
    id: task.id,
    title: task.title,
    description: task.description || '',
    status: task.status,
    assigned_to: task.assigned_to,
    assigned_to_name: task.assigned_to_name,
    weight_percent: task.weight_percent || 0,
    is_completed: task.status === 'completed' || task.status === 'done',
    completed_at: task.completed_at,
    completed_by: task.completed_by,
    completed_by_name: task.completed_by_name,
    due_date: task.due_date,
    checklist_items: task.checklist_items || [],
  };
}

/**
 * Map V2 status to internal ItemStatus
 */
function mapStatusV2(status: string): ItemStatus {
  const statusMap: Record<string, ItemStatus> = {
    'not_started': 'not_started',
    'pending': 'not_started',
    'in_progress': 'in_progress',
    'in-progress': 'in_progress',
    'completed': 'completed',
    'done': 'done',
    'blocked': 'blocked',
    'on_hold': 'on_hold',
    'on-hold': 'on_hold',
  };
  return statusMap[status] || 'not_started';
}

/**
 * Map V2 dependency type to internal LinkType
 */
function mapDependencyType(type: string): 'FS' | 'SS' | 'FF' | 'SF' {
  const typeMap: Record<string, 'FS' | 'SS' | 'FF' | 'SF'> = {
    'finish_to_start': 'FS',
    'start_to_start': 'SS',
    'finish_to_finish': 'FF',
    'start_to_finish': 'SF',
    'FS': 'FS',
    'SS': 'SS',
    'FF': 'FF',
    'SF': 'SF',
  };
  return typeMap[type] || 'FS';
}

/**
 * Transform internal GanttItem to V2 API format for saving
 */
export function toV2ItemPayload(item: Partial<GanttItem>): any {
  return {
    project: item.project_id,
    phase: item.category_id,
    name: item.title,
    description: item.description || '',
    start_date: item.start_date,
    end_date: item.end_date,
    assigned_to: item.assigned_to,
    status: item.status,
    progress: item.percent_complete,
    weight_percent: item.weight_percent,
    order: item.order,
    is_milestone: item.is_milestone,
  };
}

/**
 * Transform internal task to V2 API format
 */
export function toV2TaskPayload(task: any, itemId: number): any {
  return {
    item: itemId,
    title: task.title,
    description: task.description || '',
    status: task.status || 'pending',
    weight_percent: task.weight_percent || 0,
    assigned_to: task.assigned_to,
    due_date: task.due_date,
    order: task.order || 0,
  };
}
