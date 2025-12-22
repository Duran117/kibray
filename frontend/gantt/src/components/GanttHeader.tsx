// =============================================================================
// Kibray Gantt - GanttHeader Component
// Timeline header with date labels
// =============================================================================

import React, { useMemo } from 'react';
import { ZoomLevel, DateRange } from '../types/gantt';
import { ZOOM_CONFIG } from '../hooks/useZoom';
import { 
  isToday, 
  isWeekend, 
  isFirstOfMonth, 
  isFirstOfWeek,
  getMonthAbbr,
  getDayAbbr,
  getDaysBetween,
  addDays,
} from '../utils/dateUtils';

interface GanttHeaderProps {
  dateRange: DateRange;
  zoom: ZoomLevel;
  height: number;
}

export const GanttHeader: React.FC<GanttHeaderProps> = ({
  dateRange,
  zoom,
  height,
}) => {
  const config = ZOOM_CONFIG[zoom];
  const dayWidth = config.dayWidth;
  
  // Generate dates array from range
  const dates = useMemo(() => {
    const result: Date[] = [];
    const days = getDaysBetween(dateRange.start, dateRange.end);
    for (let i = 0; i < days; i++) {
      result.push(addDays(dateRange.start, i));
    }
    return result;
  }, [dateRange]);

  // Group dates by month for the top row
  const monthGroups = useMemo(() => {
    const groups: { month: string; year: number; days: number; startIndex: number }[] = [];
    let currentMonth = '';
    let currentYear = 0;
    let dayCount = 0;
    let startIndex = 0;

    dates.forEach((date, index) => {
      const month = getMonthAbbr(date);
      const year = date.getFullYear();
      const key = `${month}-${year}`;

      if (key !== currentMonth) {
        if (currentMonth) {
          groups.push({ 
            month: currentMonth.split('-')[0], 
            year: currentYear, 
            days: dayCount,
            startIndex 
          });
        }
        currentMonth = key;
        currentYear = year;
        dayCount = 1;
        startIndex = index;
      } else {
        dayCount++;
      }
    });

    // Push last group
    if (currentMonth) {
      groups.push({ 
        month: currentMonth.split('-')[0], 
        year: currentYear, 
        days: dayCount,
        startIndex 
      });
    }

    return groups;
  }, [dates]);

  return (
    <div 
      className="gantt-header sticky top-0 z-20 bg-white border-b border-gray-200 shadow-sm"
      style={{ height }}
    >
      {/* Month row */}
      <div className="flex h-1/2">
        {monthGroups.map((group, index) => (
          <div
            key={`${group.month}-${group.year}-${index}`}
            className="border-r border-gray-200 px-2 flex items-center text-xs font-semibold text-gray-600 bg-gray-50"
            style={{ width: group.days * dayWidth }}
          >
            {group.month} {group.year}
          </div>
        ))}
      </div>

      {/* Days row */}
      <div className="flex h-1/2">
        {dates.map((date, index) => {
          const today = isToday(date);
          const weekend = isWeekend(date);
          const firstOfMonth = isFirstOfMonth(date);
          const firstOfWeek = isFirstOfWeek(date);

          return (
            <div
              key={index}
              className={`
                flex flex-col items-center justify-center border-r text-xs
                ${today ? 'bg-blue-50 border-blue-300' : ''}
                ${weekend && !today ? 'bg-gray-50' : ''}
                ${firstOfMonth ? 'border-l-2 border-l-gray-400' : 'border-gray-200'}
              `}
              style={{ 
                width: dayWidth, 
                minWidth: dayWidth,
              }}
            >
              {/* Day of week (only for DAY/WEEK zoom) */}
              {(zoom === 'DAY' || zoom === 'WEEK') && (
                <span className={`
                  text-[10px] uppercase
                  ${today ? 'text-blue-600 font-bold' : 'text-gray-400'}
                `}>
                  {zoom === 'DAY' ? getDayAbbr(date) : (firstOfWeek ? getDayAbbr(date) : '')}
                </span>
              )}
              
              {/* Day number */}
              <span className={`
                font-medium
                ${today ? 'text-blue-600 font-bold' : 'text-gray-600'}
                ${zoom === 'MONTH' && !firstOfWeek ? 'text-gray-300' : ''}
                ${zoom === 'QUARTER' && !firstOfMonth ? 'hidden' : ''}
              `}>
                {zoom === 'QUARTER' 
                  ? (firstOfMonth ? getMonthAbbr(date).charAt(0) : '') 
                  : date.getDate()
                }
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default GanttHeader;
