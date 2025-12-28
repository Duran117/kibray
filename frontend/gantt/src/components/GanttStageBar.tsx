// =============================================================================
// Kibray Gantt - GanttStageBar Component
// Thin bar to visualize stage (phase) date range
// =============================================================================

import React from 'react';
import { GanttCategory, DateRange, ZoomLevel } from '../types/gantt';
import { calculateBarPosition, calculateBarWidth } from '../utils/positionUtils';
import { ZOOM_CONFIG } from '../hooks/useZoom';

interface GanttStageBarProps {
  category: GanttCategory;
  dateRange: DateRange;
  zoom: ZoomLevel;
  rowHeight: number;
  rowIndex: number;
  headerHeight: number;
  startDate: Date;
  endDate: Date;
}

export const GanttStageBar: React.FC<GanttStageBarProps> = ({
  category,
  dateRange,
  zoom,
  rowHeight,
  rowIndex,
  headerHeight,
  startDate,
  endDate,
}) => {
  const config = ZOOM_CONFIG[zoom];
  const left = calculateBarPosition(startDate, dateRange.start, config.dayWidth);
  const width = calculateBarWidth(startDate, endDate, config.dayWidth, 6);
  const barHeight = Math.max(6, Math.floor(rowHeight * 0.18));
  const top = headerHeight + rowIndex * rowHeight + (rowHeight - barHeight) / 2;

  return (
    <div
      className="absolute rounded-full pointer-events-none"
      style={{
        left,
        top,
        width,
        height: barHeight,
        backgroundColor: category.color || '#1F2937',
        opacity: 0.9,
      }}
    />
  );
};

export default GanttStageBar;
