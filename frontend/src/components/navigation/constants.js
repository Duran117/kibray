// Shared constants for Navigation Phase 3

export const USER_ROLES = Object.freeze({
  ADMIN: 'admin',
  PM: 'project_manager',
  ENGINEER: 'engineer',
  VIEWER: 'viewer'
});

export const TASK_STATUSES = Object.freeze({
  COMPLETED: 'completed',
  IN_PROGRESS: 'in_progress',
  BLOCKED: 'blocked'
});

export const CHANGE_ORDER_STATUS = Object.freeze({
  APPROVED: 'approved',
  PENDING: 'pending',
  REJECTED: 'rejected'
});

export const PANEL_WIDTHS = Object.freeze({
  SM: '420px',
  MD: '600px',
  LG: '760px'
});
