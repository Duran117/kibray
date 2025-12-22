// =============================================================================
// Kibray Gantt - GanttDependencyLines Component
// SVG lines showing finish-to-start dependencies between tasks
// =============================================================================

import React from 'react';
import { GanttDependency, GanttItem, ZoomLevel, DateRange } from '../types/gantt';
import { calculateBarPosition, calculateBarWidth } from '../utils/positionUtils';
import { ZOOM_CONFIG } from '../hooks/useZoom';

interface GanttDependencyLinesProps {
  dependencies: GanttDependency[];
  items: GanttItem[];
  itemRowMap: Map<number, number>; // Maps item ID to row index
  dateRange: DateRange;
  zoom: ZoomLevel;
  rowHeight: number;
  headerHeight: number;
  width: number;
  height: number;
}

interface DependencyPath {
  id: string;
  from: { x: number; y: number };
  to: { x: number; y: number };
  type: 'FS' | 'SS' | 'FF' | 'SF';
  lag: number;
  isHighlighted?: boolean;
}

export const GanttDependencyLines: React.FC<GanttDependencyLinesProps> = ({
  dependencies,
  items,
  itemRowMap,
  dateRange,
  zoom,
  rowHeight,
  headerHeight,
  width,
  height,
}) => {
  const config = ZOOM_CONFIG[zoom];
  
  // Calculate paths for all dependencies
  const paths: DependencyPath[] = React.useMemo(() => {
    return dependencies.map(dep => {
      const fromItem = items.find(i => i.id === dep.predecessor_id);
      const toItem = items.find(i => i.id === dep.successor_id);
      
      if (!fromItem || !toItem) {
        return null;
      }

      const fromRowIndex = itemRowMap.get(dep.predecessor_id);
      const toRowIndex = itemRowMap.get(dep.successor_id);
      
      if (fromRowIndex === undefined || toRowIndex === undefined) {
        return null;
      }

      const fromStartDate = new Date(fromItem.start_date);
      const fromEndDate = new Date(fromItem.end_date);
      const toStartDate = new Date(toItem.start_date);
      
      const fromLeft = calculateBarPosition(fromStartDate, dateRange.start, config.dayWidth);
      const fromWidth = calculateBarWidth(fromStartDate, fromEndDate, config.dayWidth);
      const toLeft = calculateBarPosition(toStartDate, dateRange.start, config.dayWidth);
      
      const barHeight = rowHeight - 16;
      
      // Calculate connection points based on dependency type
      let fromX: number, fromY: number, toX: number, toY: number;
      
      switch (dep.link_type) {
        case 'FS': // Finish to Start
          fromX = fromLeft + fromWidth;
          fromY = headerHeight + fromRowIndex * rowHeight + 8 + barHeight / 2;
          toX = toLeft;
          toY = headerHeight + toRowIndex * rowHeight + 8 + barHeight / 2;
          break;
        case 'SS': // Start to Start
          fromX = fromLeft;
          fromY = headerHeight + fromRowIndex * rowHeight + 8 + barHeight / 2;
          toX = toLeft;
          toY = headerHeight + toRowIndex * rowHeight + 8 + barHeight / 2;
          break;
        case 'FF': // Finish to Finish
          const toEndDate = new Date(toItem.end_date);
          const toWidth = calculateBarWidth(toStartDate, toEndDate, config.dayWidth);
          fromX = fromLeft + fromWidth;
          fromY = headerHeight + fromRowIndex * rowHeight + 8 + barHeight / 2;
          toX = toLeft + toWidth;
          toY = headerHeight + toRowIndex * rowHeight + 8 + barHeight / 2;
          break;
        case 'SF': // Start to Finish
          const toEnd = new Date(toItem.end_date);
          const toW = calculateBarWidth(toStartDate, toEnd, config.dayWidth);
          fromX = fromLeft;
          fromY = headerHeight + fromRowIndex * rowHeight + 8 + barHeight / 2;
          toX = toLeft + toW;
          toY = headerHeight + toRowIndex * rowHeight + 8 + barHeight / 2;
          break;
        default:
          fromX = fromLeft + fromWidth;
          fromY = headerHeight + fromRowIndex * rowHeight + 8 + barHeight / 2;
          toX = toLeft;
          toY = headerHeight + toRowIndex * rowHeight + 8 + barHeight / 2;
      }

      return {
        id: `dep-${dep.predecessor_id}-${dep.successor_id}`,
        from: { x: fromX, y: fromY },
        to: { x: toX, y: toY },
        type: dep.link_type,
        lag: dep.lag,
      };
    }).filter((p): p is DependencyPath => p !== null);
  }, [dependencies, items, itemRowMap, dateRange, zoom, rowHeight, headerHeight, config.dayWidth]);

  // Generate SVG path with rounded corners
  const generatePath = (path: DependencyPath): string => {
    const { from, to } = path;
    const cornerRadius = 8;
    const arrowSize = 6;
    
    // Calculate control points for a nice curved path
    const midX = from.x + 20; // Offset from the bar
    
    if (to.x > from.x + 20) {
      // Normal case: target is to the right
      return `
        M ${from.x} ${from.y}
        L ${midX} ${from.y}
        Q ${midX + cornerRadius} ${from.y} ${midX + cornerRadius} ${from.y + (to.y > from.y ? cornerRadius : -cornerRadius)}
        L ${midX + cornerRadius} ${to.y + (to.y > from.y ? -cornerRadius : cornerRadius)}
        Q ${midX + cornerRadius} ${to.y} ${midX + 2 * cornerRadius} ${to.y}
        L ${to.x - arrowSize} ${to.y}
      `.trim().replace(/\s+/g, ' ');
    } else {
      // Target is to the left or above - need to route around
      const loopOffset = 30;
      return `
        M ${from.x} ${from.y}
        L ${from.x + 10} ${from.y}
        Q ${from.x + 10 + cornerRadius} ${from.y} ${from.x + 10 + cornerRadius} ${from.y + loopOffset}
        L ${from.x + 10 + cornerRadius} ${to.y - loopOffset}
        Q ${from.x + 10 + cornerRadius} ${to.y} ${from.x + 10} ${to.y}
        L ${to.x - arrowSize} ${to.y}
      `.trim().replace(/\s+/g, ' ');
    }
  };

  if (paths.length === 0) {
    return null;
  }

  return (
    <svg 
      className="gantt-dependencies absolute inset-0 pointer-events-none overflow-visible"
      style={{ width, height }}
    >
      <defs>
        {/* Arrow marker */}
        <marker
          id="arrow"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="5"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path d="M0,0 L0,10 L10,5 z" fill="#6b7280" />
        </marker>
        
        {/* Arrow marker for highlighted dependencies */}
        <marker
          id="arrow-highlight"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="5"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path d="M0,0 L0,10 L10,5 z" fill="#3b82f6" />
        </marker>
      </defs>

      {paths.map(path => (
        <g key={path.id}>
          {/* Path line */}
          <path
            d={generatePath(path)}
            fill="none"
            stroke={path.isHighlighted ? '#3b82f6' : '#9ca3af'}
            strokeWidth={path.isHighlighted ? 2 : 1.5}
            markerEnd={path.isHighlighted ? 'url(#arrow-highlight)' : 'url(#arrow)'}
            className="transition-colors"
          />
          
          {/* Lag indicator (if any) */}
          {path.lag !== 0 && (
            <g transform={`translate(${(path.from.x + path.to.x) / 2}, ${(path.from.y + path.to.y) / 2 - 10})`}>
              <rect
                x="-12"
                y="-8"
                width="24"
                height="16"
                rx="4"
                fill="white"
                stroke="#d1d5db"
              />
              <text
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-xs fill-gray-600"
              >
                {path.lag > 0 ? `+${path.lag}d` : `${path.lag}d`}
              </text>
            </g>
          )}
        </g>
      ))}
    </svg>
  );
};

export default GanttDependencyLines;
