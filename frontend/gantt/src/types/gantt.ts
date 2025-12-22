// =============================================================================
// Kibray Unified Gantt - Type Definitions
// =============================================================================

export type GanttMode = 'project' | 'master' | 'pm' | 'strategic';

export type ItemStatus = 'not_started' | 'in_progress' | 'completed' | 'done' | 'blocked' | 'on_hold';

export type ZoomLevel = 'DAY' | 'WEEK' | 'MONTH' | 'QUARTER';

export type ViewMode = 'gantt' | 'calendar';

export type ItemType = 'category' | 'item' | 'task' | 'milestone' | 'personal';

export type LinkType = 'FS' | 'SS' | 'FF' | 'SF';

// -----------------------------------------------------------------------------
// Core Data Types
// -----------------------------------------------------------------------------

export interface DateRange {
  start: Date;
  end: Date;
}

// -----------------------------------------------------------------------------
// API Response Types
// -----------------------------------------------------------------------------

export interface GanttProject {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  color?: string;
  pm_name?: string;
  client_name?: string;
}

export interface GanttCategory {
  id: number;
  name: string;
  color: string;
  order: number;
  is_collapsed: boolean;
  project_id: number;
}

export interface GanttTask {
  id: number;
  title: string;
  status: string;
  assigned_to: number | null;
  assigned_to_name?: string;
  is_completed: boolean;
}

export interface GanttItem {
  id: number;
  title: string;
  description?: string;
  category_id: number | null;
  project_id: number;
  start_date: string;
  end_date: string;
  status: ItemStatus;
  percent_complete: number;
  is_milestone: boolean;
  is_personal: boolean;
  assigned_to?: number | null;
  assigned_to_name?: string;
  tasks?: GanttTask[];
  order: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface GanttDependency {
  id: number;
  predecessor_id: number;
  successor_id: number;
  link_type: LinkType;
  lag: number;
}

export interface GanttPermissions {
  can_view: boolean;
  can_create: boolean;
  can_edit: boolean;
  can_delete: boolean;
}

export interface GanttData {
  project?: GanttProject;
  projects?: GanttProject[];
  categories: GanttCategory[];
  items: GanttItem[];
  dependencies: GanttDependency[];
  permissions: GanttPermissions;
  metadata?: {
    items_count?: number;
    tasks_count?: number;
    dependencies_count?: number;
  };
}

// -----------------------------------------------------------------------------
// Component Props
// -----------------------------------------------------------------------------

export interface KibrayGanttProps {
  mode: GanttMode;
  projectId?: number;
  pmUserId?: number;
  showCalendarToggle?: boolean;
  defaultView?: ViewMode;
  defaultZoom?: ZoomLevel;
  apiBaseUrl?: string;
  csrfToken?: string;
  onItemClick?: (item: GanttItem) => void;
  onNavigateToDetail?: (url: string) => void;
}

export interface GanttBarProps {
  item: GanttItem;
  dayWidth: number;
  rowHeight: number;
  timelineStart: Date;
  canEdit: boolean;
  isLinking: boolean;
  isLinkSource: boolean;
  onDragEnd: (itemId: number, newStart: Date, newEnd: Date) => void;
  onResizeEnd: (itemId: number, newStart: Date, newEnd: Date) => void;
  onClick: (item: GanttItem) => void;
  onAddTask: (itemId: number) => void;
  onStartLinking: (itemId: number) => void;
  onLinkTarget: (itemId: number) => void;
}

export interface GanttRowProps {
  type: 'category' | 'item' | 'task';
  data: GanttCategory | GanttItem | GanttTask;
  depth: number;
  isCollapsed?: boolean;
  onToggleCollapse?: (id: number) => void;
  children?: React.ReactNode;
}

export interface GanttSlideOverProps {
  isOpen: boolean;
  item: GanttItem | null;
  mode: 'view' | 'edit' | 'create';
  itemType: ItemType;
  categories: GanttCategory[];
  canEdit: boolean;
  onClose: () => void;
  onSave: (data: Partial<GanttItem>) => void;
  onDelete: (itemId: number) => void;
  onAddTask: (itemId: number) => void;
  onAddDependency: (itemId: number) => void;
}

export interface CreateItemModalProps {
  isOpen: boolean;
  date: Date | null;
  showPersonalOption: boolean;
  onClose: () => void;
  onSelect: (type: ItemType) => void;
}

// -----------------------------------------------------------------------------
// Internal State Types
// -----------------------------------------------------------------------------

export interface TimelineConfig {
  startDate: Date;
  endDate: Date;
  totalDays: number;
  dayWidth: number;
  zoom: ZoomLevel;
}

export interface DragState {
  isDragging: boolean;
  itemId: number | null;
  startX: number;
  originalStart: Date | null;
  originalEnd: Date | null;
}

export interface ResizeState {
  isResizing: boolean;
  itemId: number | null;
  edge: 'left' | 'right' | null;
  startX: number;
  originalStart: Date | null;
  originalEnd: Date | null;
}

export interface LinkingState {
  isLinking: boolean;
  sourceId: number | null;
}
