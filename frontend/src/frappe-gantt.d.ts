declare module 'frappe-gantt' {
  export interface GanttOptions {
    view_mode?: 'Day' | 'Week' | 'Month' | 'Year';
    date_format?: string;
    custom_popup_html?: (task: any) => string;
    on_click?: (task: any) => void;
    on_date_change?: (task: any, start: Date, end: Date) => void;
    on_progress_change?: (task: any, progress: number) => void;
    on_view_change?: (mode: string) => void;
  }

  export interface GanttTask {
    id: string;
    name: string;
    start: string;
    end: string;
    progress: number;
    dependencies?: string;
    custom_class?: string;
  }

  export default class Gantt {
    constructor(element: string | HTMLElement, tasks: GanttTask[], options?: GanttOptions);
    change_view_mode(mode: 'Day' | 'Week' | 'Month' | 'Year'): void;
    refresh(tasks: GanttTask[]): void;
  }
}
