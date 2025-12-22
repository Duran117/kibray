// =============================================================================
// Kibray Gantt - GanttBar Component
// Draggable and resizable task bar
// =============================================================================

import React, { useRef, useState, useCallback } from 'react';
import { GanttItem, ZoomLevel, DateRange } from '../types/gantt';
import { getBarColor, getContrastTextColor } from '../utils/colorUtils';
import { calculateBarPosition, calculateBarWidth } from '../utils/positionUtils';
import { ZOOM_CONFIG } from '../hooks/useZoom';
import { formatDate } from '../utils/dateUtils';

interface GanttBarProps {
  item: GanttItem;
  dateRange: DateRange;
  zoom: ZoomLevel;
  rowHeight: number;
  rowIndex: number;
  headerHeight: number;
  isSelected: boolean;
  onClick: (item: GanttItem) => void;
  onDragEnd?: (item: GanttItem, newStartDate: Date, newEndDate: Date) => void;
  onResizeEnd?: (item: GanttItem, newEndDate: Date) => void;
  canEdit: boolean;
}

export const GanttBar: React.FC<GanttBarProps> = ({
  item,
  dateRange,
  zoom,
  rowHeight,
  rowIndex,
  headerHeight,
  isSelected,
  onClick,
  onDragEnd,
  onResizeEnd,
  canEdit,
}) => {
  const barRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  
  const config = ZOOM_CONFIG[zoom];
  const barColor = getBarColor(item.status, item.is_milestone, item.is_personal);
  const textColor = getContrastTextColor(barColor);
  
  // Calculate position and dimensions
  const startDate = new Date(item.start_date);
  const endDate = new Date(item.end_date);
  const left = calculateBarPosition(startDate, dateRange.start, config.dayWidth);
  const width = calculateBarWidth(startDate, endDate, config.dayWidth);
  const top = headerHeight + rowIndex * rowHeight + 8; // 8px padding
  const barHeight = rowHeight - 16; // 16px total vertical padding

  // Handle milestone rendering
  if (item.is_milestone) {
    return (
      <div
        ref={barRef}
        className={`gantt-bar-milestone absolute cursor-pointer transition-all ${
          isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : ''
        } hover:scale-110`}
        style={{
          left: left + width / 2 - barHeight / 2,
          top: top + barHeight / 4,
          width: barHeight / 2,
          height: barHeight / 2,
          backgroundColor: barColor,
          transform: 'rotate(45deg)',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
        }}
        onClick={(e) => {
          e.stopPropagation();
          onClick(item);
        }}
        title={`${item.title}\n${formatDate(startDate, 'short')}`}
      />
    );
  }

  // Calculate progress width
  const progressWidth = width * (item.percent_complete / 100);

  return (
    <div
      ref={barRef}
      className={`gantt-bar absolute rounded-md cursor-pointer transition-shadow group ${
        isSelected ? 'ring-2 ring-blue-500 ring-offset-1 shadow-lg' : 'shadow-sm'
      } ${isDragging ? 'opacity-75 cursor-grabbing' : ''} ${
        isResizing ? 'cursor-ew-resize' : ''
      } hover:shadow-md`}
      style={{
        left,
        top,
        width: Math.max(width, 4), // Minimum 4px width
        height: barHeight,
        backgroundColor: barColor,
        opacity: item.status === 'completed' ? 0.8 : 1,
      }}
      onClick={(e) => {
        e.stopPropagation();
        onClick(item);
      }}
      onMouseDown={(e) => {
        if (!canEdit) return;
        // Could start drag here
      }}
      title={`${item.title}\n${formatDate(startDate, 'short')} - ${formatDate(endDate, 'short')}\n${item.percent_complete}% complete`}
    >
      {/* Progress fill */}
      <div 
        className="absolute inset-0 rounded-md opacity-40 bg-white pointer-events-none"
        style={{ 
          width: `${100 - item.percent_complete}%`,
          right: 0,
          left: 'auto',
        }}
      />

      {/* Bar content */}
      <div 
        className="absolute inset-0 flex items-center px-2 overflow-hidden"
        style={{ color: textColor }}
      >
        {/* Title (only show if bar is wide enough) */}
        {width > 50 && (
          <span className="text-xs font-medium truncate flex-1">
            {item.title}
          </span>
        )}
        
        {/* Progress indicator (if wide enough) */}
        {width > 100 && (
          <span className="text-xs opacity-75 ml-2">
            {item.percent_complete}%
          </span>
        )}
      </div>

      {/* Left resize handle */}
      {canEdit && width > 20 && (
        <div 
          className="absolute left-0 top-0 bottom-0 w-2 cursor-ew-resize opacity-0 group-hover:opacity-100 bg-white/30 rounded-l-md transition-opacity"
          onMouseDown={(e) => {
            e.stopPropagation();
            // Start left resize
            setIsResizing(true);
          }}
        />
      )}

      {/* Right resize handle */}
      {canEdit && width > 20 && (
        <div 
          className="absolute right-0 top-0 bottom-0 w-2 cursor-ew-resize opacity-0 group-hover:opacity-100 bg-white/30 rounded-r-md transition-opacity"
          onMouseDown={(e) => {
            e.stopPropagation();
            // Start right resize
            setIsResizing(true);
          }}
        />
      )}

      {/* Dependency connection points */}
      {canEdit && (
        <>
          {/* Left connection point (for incoming dependencies) */}
          <div 
            className="absolute left-0 top-1/2 w-3 h-3 -ml-1.5 -mt-1.5 rounded-full bg-gray-400 border-2 border-white opacity-0 group-hover:opacity-100 cursor-crosshair shadow transition-opacity"
            title="Connect dependency here"
          />
          
          {/* Right connection point (for outgoing dependencies) */}
          <div 
            className="absolute right-0 top-1/2 w-3 h-3 -mr-1.5 -mt-1.5 rounded-full bg-blue-500 border-2 border-white opacity-0 group-hover:opacity-100 cursor-crosshair shadow transition-opacity"
            title="Drag to create dependency"
          />
        </>
      )}

      {/* Status indicator for blocked items */}
      {item.status === 'blocked' && (
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center shadow">
          <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 9v2m0 4h.01" />
          </svg>
        </div>
      )}

      {/* Overdue indicator */}
      {item.status !== 'completed' && new Date(item.end_date) < new Date() && (
        <div className="absolute -top-1 -left-1 w-4 h-4 bg-orange-500 rounded-full flex items-center justify-center shadow">
          <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 8v4l3 3" />
          </svg>
        </div>
      )}
    </div>
  );
};

export default GanttBar;
