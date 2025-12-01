export interface ScheduleTask {
  id: number;
  name: string;
  start: string;
  end: string;
  progress: number;
}

export interface ScheduleCategory {
  id: number;
  name: string;
}

export interface TaskFormData {
  name: string;
  start: string;
  end: string;
  category?: number;
}
