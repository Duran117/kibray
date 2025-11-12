export interface ScheduleTask {
  id: string;
  name: string;
  start: string;
  end: string;
  progress: number;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'BLOCKED' | 'DONE';
  dependencies?: string[];
  category?: number;
  is_milestone?: boolean;
  custom_class?: string;
}

export interface ScheduleCategory {
  id: number;
  name: string;
  order: number;
  percent_complete: number;
}

export interface GanttTask {
  id: string;
  name: string;
  start: string;
  end: string;
  progress: number;
  dependencies: string;
  custom_class: string;
}

export interface TaskFormData {
  name: string;
  start: string;
  end: string;
  status: string;
  progress: number;
  category?: number;
  is_milestone?: boolean;
  description?: string;
}
