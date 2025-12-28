// =============================================================================
// Kibray Gantt - GanttGrid Component
// Timeline grid with day columns and click-to-create functionality
// =============================================================================

import React, { useRef, useCallback } from 'react';
import { ZoomLevel, DateRange } from '../types/gantt';
import { getDaysBetween, isWeekend, isToday, addDays } from '../utils/dateUtils';
import { ZOOM_CONFIG } from '../hooks/useZoom';

interface GanttGridProps {
  dateRange: DateRange;
  zoom: ZoomLevel;
  rowHeight: number;
  rowCount: number;
  headerHeight: number;
  onClick: (date: Date, rowIndex: number) => void;
  onMouseMove?: (date: Date, rowIndex: number) => void;
}

export const GanttGrid: React.FC<GanttGridProps> = ({
  dateRange,
  zoom,
  rowHeight,
  rowCount,
  headerHeight,
  onClick,
  onMouseMove,
}) => {
  const gridRef = useRef<HTMLDivElement>(null);
  const config = ZOOM_CONFIG[zoom];
  
  // Calculate grid dimensions
  const days = getDaysBetween(dateRange.start, dateRange.end);
  const gridWidth = days * config.dayWidth;
  const gridHeight = rowCount * rowHeight;

  // Generate day columns
  const dayColumns = React.useMemo(() => {
    const columns: { date: Date; isWeekend: boolean; isToday: boolean }[] = [];
    let currentDate = new Date(dateRange.start);
    
    for (let i = 0; i < days; i++) {
      columns.push({
        date: new Date(currentDate),
        isWeekend: isWeekend(currentDate),
        isToday: isToday(currentDate),
      });
      currentDate = addDays(currentDate, 1);
    }
    
    return columns;
  }, [dateRange, days]);

  // Handle click on grid
  const handleClick = useCallback((e: React.MouseEvent) => {
    console.log('[GanttGrid] handleClick called');
    if (!gridRef.current) {
      console.log('[GanttGrid] No gridRef');
      return;
    }
    
    const rect = gridRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left + gridRef.current.scrollLeft;
    const y = e.clientY - rect.top - headerHeight;
    
    console.log('[GanttGrid] Click coordinates:', { x, y, headerHeight });
    
    if (y < 0) {
      console.log('[GanttGrid] Click was on header, ignoring');
      return; // Click was on header
    }
    
    const dayIndex = Math.floor(x / config.dayWidth);
    const rowIndex = Math.floor(y / rowHeight);
    
    console.log('[GanttGrid] Calculated:', { dayIndex, rowIndex, days, rowCount });
    
    if (dayIndex >= 0 && dayIndex < days && rowIndex >= 0 && rowIndex < rowCount) {
      const clickedDate = addDays(dateRange.start, dayIndex);
      console.log('[GanttGrid] Calling onClick with:', { clickedDate, rowIndex });
      onClick(clickedDate, rowIndex);
    } else {
      console.log('[GanttGrid] Click out of bounds');
    }
  }, [config.dayWidth, rowHeight, headerHeight, days, rowCount, dateRange, onClick]);

  // Handle mouse move (for hover effects, previews)
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!gridRef.current || !onMouseMove) return;
    
    const rect = gridRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left + gridRef.current.scrollLeft;
    const y = e.clientY - rect.top - headerHeight;
    
    if (y < 0) return;
    
    const dayIndex = Math.floor(x / config.dayWidth);
    const rowIndex = Math.floor(y / rowHeight);
    
    if (dayIndex >= 0 && dayIndex < days && rowIndex >= 0 && rowIndex < rowCount) {
      const hoverDate = addDays(dateRange.start, dayIndex);
      onMouseMove(hoverDate, rowIndex);
    }
  }, [config.dayWidth, rowHeight, headerHeight, days, rowCount, dateRange, onMouseMove]);

  return (
    <div 
      ref={gridRef}
      className="gantt-grid absolute inset-0 overflow-hidden"
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      style={{ cursor: 'crosshair' }}
    >
      {/* Vertical day lines */}
      <svg 
        className="absolute pointer-events-none"
        style={{ 
          width: gridWidth, 
          height: gridHeight + headerHeight,
          top: 0,
          left: 0 
        }}
      >
        {/* Day column backgrounds */}
        {dayColumns.map((col, index) => (
          <rect
            key={`bg-${index}`}
            x={index * config.dayWidth}
            y={headerHeight}
            width={config.dayWidth}
            height={gridHeight}
            fill={col.isToday ? 'rgba(59, 130, 246, 0.1)' : col.isWeekend ? 'rgba(0, 0, 0, 0.02)' : 'transparent'}
          />
        ))}

        {/* Vertical grid lines */}
        {dayColumns.map((col, index) => (
          <line
            key={`line-${index}`}
            x1={index * config.dayWidth}
            y1={headerHeight}
            x2={index * config.dayWidth}
            y2={gridHeight + headerHeight}
            stroke={col.isToday ? 'rgba(59, 130, 246, 0.5)' : '#e5e7eb'}
            strokeWidth={col.isToday ? 2 : 1}
          />
        ))}

        {/* Horizontal row lines */}
        {Array.from({ length: rowCount + 1 }).map((_, index) => (
          <line
            key={`row-${index}`}
            x1={0}
            y1={headerHeight + index * rowHeight}
            x2={gridWidth}
            y2={headerHeight + index * rowHeight}
            stroke="#f3f4f6"
            strokeWidth={1}
          />
        ))}

        {/* Today marker line */}
        {dayColumns.map((col, index) => 
          col.isToday && (
            <line
              key={`today-marker`}
              x1={index * config.dayWidth + config.dayWidth / 2}
              y1={0}
              x2={index * config.dayWidth + config.dayWidth / 2}
              y2={gridHeight + headerHeight}
              stroke="#3b82f6"
              strokeWidth={2}
              strokeDasharray="4,4"
            />
          )
        )}
      </svg>

      {/* Today indicator badge */}
      {dayColumns.map((col, index) => 
        col.isToday && (
          <div
            key="today-badge"
            className="absolute bg-blue-500 text-white text-xs font-semibold px-2 py-0.5 rounded-full shadow-sm pointer-events-none"
            style={{
              left: index * config.dayWidth + config.dayWidth / 2,
              top: headerHeight - 4,
              transform: 'translate(-50%, -100%)'
            }}
          >
            Today
          </div>
        )
      )}
    </div>
  );
};

export default GanttGrid;
