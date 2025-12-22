// =============================================================================
// Kibray Gantt - Position Utilities
// =============================================================================

import { parseDate, getDaysBetween } from './dateUtils';

/**
 * Calculate the left position (in pixels) of a bar relative to timeline start
 * Accepts either Date object or string
 */
export function calculateBarPosition(
  itemStartDate: Date | string,
  timelineStart: Date,
  dayWidth: number
): number {
  const start = typeof itemStartDate === 'string' ? parseDate(itemStartDate) : itemStartDate;
  const daysFromStart = getDaysBetween(timelineStart, start);
  return daysFromStart * dayWidth;
}

/**
 * Calculate the left position (in pixels) of a bar relative to timeline start
 * @deprecated Use calculateBarPosition instead
 */
export function calculateBarLeft(
  itemStartDate: string,
  timelineStart: Date,
  dayWidth: number
): number {
  const start = parseDate(itemStartDate);
  const daysFromStart = getDaysBetween(timelineStart, start) - 1;
  return daysFromStart * dayWidth;
}

/**
 * Calculate the width (in pixels) of a bar
 * Accepts either Date objects or strings
 */
export function calculateBarWidth(
  itemStartDate: Date | string,
  itemEndDate: Date | string,
  dayWidth: number,
  minWidth: number = 20
): number {
  const start = typeof itemStartDate === 'string' ? parseDate(itemStartDate) : itemStartDate;
  const end = typeof itemEndDate === 'string' ? parseDate(itemEndDate) : itemEndDate;
  const days = getDaysBetween(start, end) + 1; // Include end date
  return Math.max(days * dayWidth, minWidth);
}

/**
 * Calculate date from pixel position
 */
export function calculateDateFromPosition(
  pixelX: number,
  timelineStart: Date,
  dayWidth: number
): Date {
  const daysOffset = Math.round(pixelX / dayWidth);
  const result = new Date(timelineStart);
  result.setDate(result.getDate() + daysOffset);
  return result;
}

/**
 * Snap position to day grid
 */
export function snapToGrid(pixelX: number, dayWidth: number): number {
  return Math.round(pixelX / dayWidth) * dayWidth;
}

/**
 * Calculate the position for the today line
 */
export function calculateTodayLinePosition(
  timelineStart: Date,
  dayWidth: number
): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const daysFromStart = getDaysBetween(timelineStart, today) - 1;
  // Position in the middle of today's column
  return daysFromStart * dayWidth + dayWidth / 2;
}

/**
 * Check if today is within the visible timeline
 */
export function isTodayInTimeline(
  timelineStart: Date,
  timelineEnd: Date
): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today >= timelineStart && today <= timelineEnd;
}

/**
 * Calculate row Y position based on index and row height
 */
export function calculateRowY(index: number, rowHeight: number): number {
  return index * rowHeight;
}

/**
 * Get the item index at a given Y position
 */
export function getItemIndexAtY(y: number, rowHeight: number): number {
  return Math.floor(y / rowHeight);
}

/**
 * Calculate milestone diamond position (center of the day)
 */
export function calculateMilestonePosition(
  itemStartDate: string,
  timelineStart: Date,
  dayWidth: number
): number {
  const left = calculateBarLeft(itemStartDate, timelineStart, dayWidth);
  return left + dayWidth / 2;
}

/**
 * Calculate dependency line path between two items
 */
export function calculateDependencyPath(
  predecessorLeft: number,
  predecessorWidth: number,
  predecessorY: number,
  successorLeft: number,
  successorY: number,
  rowHeight: number
): string {
  // Start from the end of predecessor bar
  const startX = predecessorLeft + predecessorWidth;
  const startY = predecessorY + rowHeight / 2;
  
  // End at the start of successor bar
  const endX = successorLeft;
  const endY = successorY + rowHeight / 2;
  
  // Calculate control points for a smooth curve
  const midX = (startX + endX) / 2;
  
  // If successor is below predecessor, curve down
  if (endY > startY) {
    return `M ${startX} ${startY} 
            C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
  }
  
  // If successor is above, curve up
  return `M ${startX} ${startY} 
          C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
}

/**
 * Calculate arrow head points for dependency line
 */
export function calculateArrowHead(
  endX: number,
  endY: number,
  size: number = 8
): string {
  return `M ${endX} ${endY} 
          L ${endX - size} ${endY - size / 2} 
          L ${endX - size} ${endY + size / 2} Z`;
}
