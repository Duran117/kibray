// =============================================================================
// Kibray Gantt - GanttBar Component (Phase 2 - Interactive)
// Draggable and resizable task bar with full interactivity
// =============================================================================

import React, { useRef, useState, useCallback } from 'react';
import { GanttItem, ZoomLevel, DateRange } from '../types/gantt';
import { getBarColor, getContrastTextColor } from '../utils/colorUtils';
import { calculateBarPosition, calculateBarWidth } from '../utils/positionUtils';
import { ZOOM_CONFIG } from '../hooks/useZoom';
import { formatDate } from '../utils/dateUtils';
import { DragType } from '../hooks/useDragAndDrop';

interface GanttBarProps {
  item: GanttItem;
  dateRange: DateRange;
  zoom: ZoomLevel;
  rowHeight: number;
  rowIndex: number;
  headerHeight: number;
  isSelected: boolean;
  isDragging: boolean;
  previewDates?: { start: Date; end: Date } | null;
  onClick: (item: GanttItem) => void;
  onDragStart: (e: React.MouseEvent, item: GanttItem, type: DragType) => void;
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
  isDragging,
  previewDates,
  onClick,
  onDragStart,
  canEdit,
}) => {
  const barRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  
  const config = ZOOM_CONFIG[zoom];
  const barColor = getBarColor(item.status, item.is_milestone, item.is_personal);
  const textColor = getContrastTextColor(barColor);
  
  // Use preview dates if dragging, otherwise use item dates
  const startDate = previewDates?.start || new Date(item.start_date);
  const endDate = previewDates?.end || new Date(item.end_date);
  
  // Calculate position and dimensions
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
        onMouseDown={(e) => {
          if (canEdit && e.button === 0) {
            onDragStart(e, item, 'move');
          }
        }}
        title={`${item.title}\n${formatDate(startDate, 'short')}`}
      />
    );
  }

  return (
    <div
      ref={barRef}
      className={`gantt-bar absolute rounded-md cursor-grab group ${
        isSelected ? 'ring-2 ring-blue-500 ring-offset-1 shadow-lg z-10' : ''
      } ${isDragging ? 'opacity-80 cursor-grabbing shadow-xl z-20' : ''} 
      hover:shadow-md transition-shadow`}
      style={{
        left,
        top,
        width: Math.max(width, 4), // Minimum 4px width
        height: barHeight,
        backgroundColor: barColor,
        opacity: item.status === 'completed' ? 0.85 : 1,
      }}
      onClick={(e) => {
        if (!isDragging) {
          e.stopPropagation();
          onClick(item);
        }
      }}
      onMouseDown={(e) => {
        if (canEdit && e.button === 0) {
          onDragStart(e, item, 'move');
        }
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      title={`${item.title}\n${formatDate(startDate, 'short')} - ${formatDate(endDate, 'short')}\n${item.percent_complete}% complete`}
    >
      {/* Progress fill (darker overlay on incomplete portion) */}
      <div 
        className="absolute inset-0 rounded-md pointer-events-none"
        style={{ 
          background: `linear-gradient(to right, 
            transparent ${item.percent_complete}%, 
            rgba(255,255,255,0.3) ${item.percent_complete}%
          )`,
        }}
      />

      {/* Bar content */}
      <div 
        className="absolute inset-0 flex items-center px-2 overflow-hidden pointer-events-none"
        style={{ color: textColor }}
      >
        {/* Title (only show if bar is wide enough) */}
        {width > 60 && (
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
      {canEdit && width > 30 && (
        <div 
          className={`absolute left-0 top-0 bottom-0 w-3 cursor-ew-resize rounded-l-md transition-all ${
            isHovered || isDragging ? 'bg-black/20' : 'bg-transparent'
          }`}
          onMouseDown={(e) => {
            e.stopPropagation();
            onDragStart(e, item, 'resize-left');
          }}
        >
          {/* Grip lines */}
          {isHovered && (
            <div className="absolute inset-y-0 left-1 flex flex-col justify-center gap-0.5">
              <div className="w-0.5 h-2 bg-white/50 rounded-full" />
              <div className="w-0.5 h-2 bg-white/50 rounded-full" />
            </div>
          )}
        </div>
      )}

      {/* Right resize handle */}
      {canEdit && width > 30 && (
        <div 
          className={`absolute right-0 top-0 bottom-0 w-3 cursor-ew-resize rounded-r-md transition-all ${
            isHovered || isDragging ? 'bg-black/20' : 'bg-transparent'
          }`}
          onMouseDown={(e) => {
            e.stopPropagation();
            onDragStart(e, item, 'resize-right');
          }}
        >
          {/* Grip lines */}
          {isHovered && (
            <div className="absolute inset-y-0 right-1 flex flex-col justify-center gap-0.5">
              <div className="w-0.5 h-2 bg-white/50 rounded-full" />
              <div className="w-0.5 h-2 bg-white/50 rounded-full" />
            </div>
          )}
        </div>
      )}

      {/* Status indicator for blocked items */}
      {item.status === 'blocked' && (
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center shadow pointer-events-none">
          <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 9v2m0 4h.01" />
          </svg>
        </div>
      )}

      {/* Overdue indicator */}
      {item.status !== 'completed' && new Date(item.end_date) < new Date() && (
        <div className="absolute -top-1 -left-1 w-4 h-4 bg-orange-500 rounded-full flex items-center justify-center shadow pointer-events-none">
          <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 8v4l3 3" />
          </svg>
        </div>
      )}

      {/* Drag preview tooltip */}
      {isDragging && previewDates && (
        <div 
          className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg whitespace-nowrap pointer-events-none z-30"
        >
          {formatDate(previewDates.start, 'short')} - {formatDate(previewDates.end, 'short')}
        </div>
      )}
    </div>
  );
};

export default GanttBar;
