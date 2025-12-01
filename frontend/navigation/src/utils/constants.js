export const WIDGET_COLORS = {
  blue: { bg: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' },
  green: { bg: 'rgba(16, 185, 129, 0.1)', color: '#10b981' },
  orange: { bg: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' },
  purple: { bg: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6' },
  red: { bg: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' },
  cyan: { bg: 'rgba(6, 182, 212, 0.1)', color: '#06b6d4' }
};

export const ALERT_TYPES = {
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
  SUCCESS: 'success'
};

export const TASK_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  BLOCKED: 'blocked',
  ON_HOLD: 'on_hold'
};

export const TASK_PRIORITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

export const CO_STATUS = {
  DRAFT: 'draft',
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled'
};

export const ROLES = {
  ADMIN: 'admin',
  PM: 'pm',
  SUPERINTENDENT: 'superintendent',
  EMPLOYEE: 'employee',
  CLIENT: 'client',
  DESIGNER: 'designer',
  ACCOUNTANT: 'accountant'
};

export const BREAKPOINTS = {
  xs: 480,
  sm: 768,
  md: 996,
  lg: 1200,
  xl: 1600,
  xxl: 1920
};

export const GRID_COLS = {
  lg: 12,
  md: 10,
  sm: 6,
  xs: 4,
  xxs: 2
};

export const PANEL_WIDTHS = {
  SMALL: '400px',
  MEDIUM: '600px',
  LARGE: '800px',
  XLARGE: '1000px'
};

// Phase 4 Constants
export const FILE_CATEGORIES = {
  DRAWINGS: 'drawings',
  PHOTOS: 'photos',
  INVOICES: 'invoices',
  CHANGE_ORDERS: 'change-orders',
  CONTRACTS: 'contracts',
  REPORTS: 'reports',
  OTHER: 'other'
};

export const FILE_MAX_SIZE = 10 * 1024 * 1024; // 10MB

export const ALLOWED_FILE_TYPES = [
  'image/*',
  'application/pdf',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
];

export const USER_PERMISSIONS = {
  VIEW_PROJECTS: 'view_projects',
  EDIT_PROJECTS: 'edit_projects',
  DELETE_PROJECTS: 'delete_projects',
  VIEW_FINANCIALS: 'view_financials',
  EDIT_FINANCIALS: 'edit_financials',
  MANAGE_USERS: 'manage_users',
  UPLOAD_FILES: 'upload_files',
  DELETE_FILES: 'delete_files',
  VIEW_REPORTS: 'view_reports',
  EXPORT_DATA: 'export_data'
};

export const NOTIFICATION_TYPES = {
  INFO: 'info',
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error',
  TASK_ASSIGNED: 'task_assigned',
  COMMENT_ADDED: 'comment_added',
  FILE_UPLOADED: 'file_uploaded',
  STATUS_CHANGED: 'status_changed'
};

export const CHAT_MESSAGE_TYPES = {
  TEXT: 'text',
  FILE: 'file',
  IMAGE: 'image',
  SYSTEM: 'system'
};

export const REPORT_TYPES = {
  PROJECT_SUMMARY: 'project_summary',
  FINANCIAL: 'financial',
  TIMESHEET: 'timesheet',
  TASK_REPORT: 'task_report',
  CUSTOM: 'custom'
};

export const CHART_TYPES = {
  LINE: 'line',
  BAR: 'bar',
  PIE: 'pie',
  DOUGHNUT: 'doughnut',
  AREA: 'area'
};

export const TIME_RANGES = {
  TODAY: 'today',
  WEEK: '7d',
  MONTH: '30d',
  QUARTER: '90d',
  YEAR: '1y',
  ALL: 'all'
};
