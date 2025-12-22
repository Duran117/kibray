// =============================================================================
// Kibray Gantt - Date Utilities
// =============================================================================

import { ZoomLevel } from '../types/gantt';

/**
 * Parse ISO date string to Date object (handles timezone correctly)
 */
export function parseDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day);
}

/**
 * Format Date to string based on format type
 * @param date - The date to format
 * @param format - 'iso' (YYYY-MM-DD), 'short' (Dec 20), 'full' (Dec 20, 2025)
 */
export function formatDate(date: Date, format: 'iso' | 'short' | 'full' = 'iso'): string {
  switch (format) {
    case 'short':
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    case 'full':
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    case 'iso':
    default:
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
  }
}

/**
 * Format date for display (e.g., "Dec 20")
 */
export function formatDateShort(date: Date): string {
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Format date for display with year (e.g., "Dec 20, 2025")
 */
export function formatDateLong(date: Date): string {
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
  });
}

/**
 * Get day of week abbreviation (Mon, Tue, etc.)
 */
export function getDayAbbr(date: Date): string {
  return date.toLocaleDateString('en-US', { weekday: 'short' });
}

/**
 * Get month abbreviation (Jan, Feb, etc.)
 */
export function getMonthAbbr(date: Date): string {
  return date.toLocaleDateString('en-US', { month: 'short' });
}

/**
 * Check if two dates are the same day
 */
export function isSameDay(date1: Date, date2: Date): boolean {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  );
}

/**
 * Check if date is today
 */
export function isToday(date: Date): boolean {
  return isSameDay(date, new Date());
}

/**
 * Check if date is a weekend (Saturday or Sunday)
 */
export function isWeekend(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6;
}

/**
 * Check if date is the first day of the month
 */
export function isFirstOfMonth(date: Date): boolean {
  return date.getDate() === 1;
}

/**
 * Check if date is the first day of the week (Monday)
 */
export function isFirstOfWeek(date: Date): boolean {
  return date.getDay() === 1;
}

/**
 * Add days to a date
 */
export function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

/**
 * Get number of days between two dates (inclusive)
 */
export function getDaysBetween(start: Date, end: Date): number {
  const diffTime = end.getTime() - start.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
}

/**
 * Get array of dates between start and end (inclusive)
 */
export function getDateRange(start: Date, end: Date): Date[] {
  const dates: Date[] = [];
  const current = new Date(start);
  
  while (current <= end) {
    dates.push(new Date(current));
    current.setDate(current.getDate() + 1);
  }
  
  return dates;
}

/**
 * Get the start of the week (Monday) for a given date
 */
export function getWeekStart(date: Date): Date {
  const result = new Date(date);
  const day = result.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  result.setDate(result.getDate() + diff);
  return result;
}

/**
 * Get the start of the month for a given date
 */
export function getMonthStart(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

/**
 * Get the start of the quarter for a given date
 */
export function getQuarterStart(date: Date): Date {
  const quarter = Math.floor(date.getMonth() / 3);
  return new Date(date.getFullYear(), quarter * 3, 1);
}

/**
 * Calculate timeline boundaries with padding
 */
export function calculateTimelineBounds(
  items: { start_date: string; end_date: string }[],
  padding: number = 7
): { start: Date; end: Date } {
  if (items.length === 0) {
    const today = new Date();
    return {
      start: addDays(today, -padding),
      end: addDays(today, 30 + padding),
    };
  }

  let minDate = parseDate(items[0].start_date);
  let maxDate = parseDate(items[0].end_date);

  items.forEach((item) => {
    const start = parseDate(item.start_date);
    const end = parseDate(item.end_date);
    if (start < minDate) minDate = start;
    if (end > maxDate) maxDate = end;
  });

  return {
    start: addDays(minDate, -padding),
    end: addDays(maxDate, padding),
  };
}

/**
 * Get day width based on zoom level
 */
export function getDayWidth(zoom: ZoomLevel): number {
  switch (zoom) {
    case 'DAY':
      return 60;
    case 'WEEK':
      return 30;
    case 'MONTH':
      return 10;
    case 'QUARTER':
      return 3;
    default:
      return 30;
  }
}

/**
 * Get header labels based on zoom level
 */
export function getHeaderLabels(
  startDate: Date,
  endDate: Date,
  zoom: ZoomLevel
): { date: Date; label: string; isMain: boolean }[] {
  const labels: { date: Date; label: string; isMain: boolean }[] = [];
  const dates = getDateRange(startDate, endDate);

  dates.forEach((date) => {
    switch (zoom) {
      case 'DAY':
        labels.push({
          date,
          label: `${getDayAbbr(date)}\n${date.getDate()}`,
          isMain: isFirstOfMonth(date),
        });
        break;
      case 'WEEK':
        labels.push({
          date,
          label: String(date.getDate()),
          isMain: isFirstOfWeek(date) || isFirstOfMonth(date),
        });
        break;
      case 'MONTH':
        labels.push({
          date,
          label: isFirstOfWeek(date) ? String(date.getDate()) : '',
          isMain: isFirstOfMonth(date),
        });
        break;
      case 'QUARTER':
        labels.push({
          date,
          label: isFirstOfMonth(date) ? getMonthAbbr(date) : '',
          isMain: isFirstOfMonth(date),
        });
        break;
    }
  });

  return labels;
}
