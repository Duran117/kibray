// =============================================================================
// Kibray Gantt - Color Utilities
// =============================================================================

import { ItemStatus } from '../types/gantt';

/**
 * Status color palette (Monday.com inspired)
 */
export const STATUS_COLORS: Record<ItemStatus, { bg: string; border: string; text: string }> = {
  not_started: {
    bg: '#f1f5f9',      // slate-100
    border: '#94a3b8',  // slate-400
    text: '#475569',    // slate-600
  },
  in_progress: {
    bg: '#dbeafe',      // blue-100
    border: '#3b82f6',  // blue-500
    text: '#1d4ed8',    // blue-700
  },
  completed: {
    bg: '#dcfce7',      // green-100
    border: '#22c55e',  // green-500
    text: '#15803d',    // green-700
  },
  done: {
    bg: '#dcfce7',      // green-100
    border: '#22c55e',  // green-500
    text: '#15803d',    // green-700
  },
  blocked: {
    bg: '#fee2e2',      // red-100
    border: '#ef4444',  // red-500
    text: '#b91c1c',    // red-700
  },
  on_hold: {
    bg: '#fef3c7',      // amber-100
    border: '#f59e0b',  // amber-500
    text: '#b45309',    // amber-700
  },
};

/**
 * Bar fill colors (solid, for the gantt bars)
 */
export const STATUS_BAR_COLORS: Record<ItemStatus, string> = {
  not_started: '#94a3b8',  // slate-400
  in_progress: '#3b82f6',  // blue-500
  completed: '#22c55e',    // green-500
  done: '#22c55e',         // green-500
  blocked: '#ef4444',      // red-500
  on_hold: '#f59e0b',      // amber-500
};

/**
 * Milestone color
 */
export const MILESTONE_COLOR = '#8b5cf6'; // violet-500

/**
 * Personal event color
 */
export const PERSONAL_COLOR = '#f59e0b'; // amber-500

/**
 * Today line color
 */
export const TODAY_LINE_COLOR = '#f97316'; // orange-500

/**
 * Dependency line color
 */
export const DEPENDENCY_LINE_COLOR = '#6b7280'; // gray-500

/**
 * Weekend background color
 */
export const WEEKEND_BG_COLOR = '#f8fafc'; // slate-50

/**
 * Hover highlight color
 */
export const HOVER_HIGHLIGHT_COLOR = '#eff6ff'; // blue-50

/**
 * Category colors palette (for auto-assignment)
 */
export const CATEGORY_COLORS = [
  '#3b82f6', // blue-500
  '#22c55e', // green-500
  '#f59e0b', // amber-500
  '#ef4444', // red-500
  '#8b5cf6', // violet-500
  '#06b6d4', // cyan-500
  '#ec4899', // pink-500
  '#84cc16', // lime-500
  '#f97316', // orange-500
  '#6366f1', // indigo-500
];

/**
 * Get bar color based on item properties
 */
export function getBarColor(
  status: ItemStatus,
  isMilestone: boolean,
  isPersonal: boolean
): string {
  if (isMilestone) return MILESTONE_COLOR;
  if (isPersonal) return PERSONAL_COLOR;
  return STATUS_BAR_COLORS[status];
}

/**
 * Get status label
 */
export function getStatusLabel(status: ItemStatus): string {
  switch (status) {
    case 'not_started':
      return 'Not Started';
    case 'in_progress':
      return 'In Progress';
    case 'completed':
      return 'Completed';
    case 'done':
      return 'Done';
    case 'blocked':
      return 'Blocked';
    case 'on_hold':
      return 'On Hold';
    default:
      return status;
  }
}

/**
 * Get next category color (cycles through palette)
 */
export function getNextCategoryColor(existingColors: string[]): string {
  for (const color of CATEGORY_COLORS) {
    if (!existingColors.includes(color)) {
      return color;
    }
  }
  // If all colors used, start over
  return CATEGORY_COLORS[existingColors.length % CATEGORY_COLORS.length];
}

/**
 * Darken a hex color by percentage
 */
export function darkenColor(hex: string, percent: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const amt = Math.round(2.55 * percent);
  const R = (num >> 16) - amt;
  const G = ((num >> 8) & 0x00ff) - amt;
  const B = (num & 0x0000ff) - amt;
  return `#${(
    0x1000000 +
    (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
    (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
    (B < 255 ? (B < 1 ? 0 : B) : 255)
  )
    .toString(16)
    .slice(1)}`;
}

/**
 * Lighten a hex color by percentage
 */
export function lightenColor(hex: string, percent: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const amt = Math.round(2.55 * percent);
  const R = (num >> 16) + amt;
  const G = ((num >> 8) & 0x00ff) + amt;
  const B = (num & 0x0000ff) + amt;
  return `#${(
    0x1000000 +
    (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
    (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
    (B < 255 ? (B < 1 ? 0 : B) : 255)
  )
    .toString(16)
    .slice(1)}`;
}

/**
 * Get contrasting text color (black or white) for a given background
 */
export function getContrastTextColor(hexBg: string): string {
  const hex = hexBg.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  // Calculate relative luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  
  return luminance > 0.5 ? '#1f2937' : '#ffffff';
}

/**
 * Get Tailwind-like bg class for status
 */
export function getStatusBgClass(status: ItemStatus): string {
  switch (status) {
    case 'not_started':
      return 'bg-slate-100';
    case 'in_progress':
      return 'bg-blue-100';
    case 'done':
      return 'bg-green-100';
    case 'blocked':
      return 'bg-red-100';
    default:
      return 'bg-gray-100';
  }
}

/**
 * Get category color by ID (deterministic based on index)
 */
export function getCategoryColor(index: number): string {
  return CATEGORY_COLORS[index % CATEGORY_COLORS.length];
}
