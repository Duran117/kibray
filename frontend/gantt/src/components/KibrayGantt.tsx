// =============================================================================
// Kibray Gantt - Main Component
// Unified Gantt chart component with Monday.com-style UX
// =============================================================================

import React, { useState, useRef, useCallback, useMemo, useEffect } from 'react';
import {
  GanttMode,
  ViewMode,
  ZoomLevel,
  GanttItem,
  GanttCategory,
  GanttDependency,
  DateRange,
} from '../types/gantt';
import { useZoom, ZOOM_CONFIG } from '../hooks/useZoom';
import { getDaysBetween, addDays } from '../utils/dateUtils';

// Components
import { GanttToolbar } from './GanttToolbar';
import { GanttHeader } from './GanttHeader';
import { GanttSidebar } from './GanttSidebar';
import { GanttGrid } from './GanttGrid';
import { GanttBar } from './GanttBar';
import { GanttDependencyLines } from './GanttDependencyLines';
import { SlideOverPanel } from './SlideOverPanel';

// Constants
const SIDEBAR_WIDTH = 280;
const ROW_HEIGHT = 48;
const HEADER_HEIGHT = 80;

export interface KibrayGanttProps {
  // Mode determines the context (project, master, strategic, pm)
  mode: GanttMode;
  
  // Data
  items: GanttItem[];
  categories: GanttCategory[];
  dependencies: GanttDependency[];
  
  // Context info
  projectId?: number;
  projectName?: string;
  
  // Permissions
  canEdit?: boolean;
  
  // Callbacks
  onItemCreate?: (item: Partial<GanttItem>) => Promise<GanttItem>;
  onItemUpdate?: (item: Partial<GanttItem>) => Promise<void>;
  onItemDelete?: (itemId: number) => Promise<void>;
  onDependencyCreate?: (dep: Partial<GanttDependency>) => Promise<void>;
  onDependencyDelete?: (depId: number) => Promise<void>;
  
  // Optional date range override
  initialDateRange?: DateRange;
  
  // Initial zoom level
  initialZoom?: ZoomLevel;
}

export const KibrayGantt: React.FC<KibrayGanttProps> = ({
  mode,
  items,
  categories,
  dependencies,
  projectId,
  projectName,
  canEdit = false,
  onItemCreate,
  onItemUpdate,
  onItemDelete,
  onDependencyCreate,
  onDependencyDelete,
  initialDateRange,
  initialZoom = 'WEEK',
}) => {
  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  // State
  const [viewMode, setViewMode] = useState<ViewMode>('gantt');
  const [collapsedCategories, setCollapsedCategories] = useState<Set<number>>(new Set());
  const [selectedItem, setSelectedItem] = useState<GanttItem | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const { zoom, setZoom } = useZoom(initialZoom);

  // Calculate date range from items or use default
  const dateRange = useMemo<DateRange>(() => {
    if (initialDateRange) return initialDateRange;

    if (items.length === 0) {
      // Default: 2 months centered on today
      const today = new Date();
      return {
        start: addDays(today, -15),
        end: addDays(today, 45),
      };
    }

    // Find min and max dates from items
    let minDate = new Date(items[0].start_date);
    let maxDate = new Date(items[0].end_date);

    items.forEach(item => {
      const start = new Date(item.start_date);
      const end = new Date(item.end_date);
      if (start < minDate) minDate = start;
      if (end > maxDate) maxDate = end;
    });

    // Add padding (7 days before, 14 days after)
    return {
      start: addDays(minDate, -7),
      end: addDays(maxDate, 14),
    };
  }, [items, initialDateRange]);

  // Build flat list of visible rows (respecting collapsed state)
  const visibleRows = useMemo(() => {
    const rows: { type: 'category' | 'item'; data: GanttCategory | GanttItem }[] = [];
    
    const sortedCategories = [...categories].sort((a, b) => a.order - b.order);
    const orphanItems = items.filter(i => !i.category_id).sort((a, b) => a.order - b.order);

    sortedCategories.forEach(category => {
      rows.push({ type: 'category', data: category });

      if (!collapsedCategories.has(category.id)) {
        const categoryItems = items
          .filter(i => i.category_id === category.id)
          .sort((a, b) => a.order - b.order);
        categoryItems.forEach(item => {
          rows.push({ type: 'item', data: item });
        });
      }
    });

    if (orphanItems.length > 0) {
      // Virtual "Uncategorized" category
      rows.push({
        type: 'category',
        data: { id: -1, name: 'Uncategorized', color: '#6b7280', order: 9999, is_collapsed: false, project_id: projectId || 0 } as GanttCategory,
      });
      orphanItems.forEach(item => {
        rows.push({ type: 'item', data: item });
      });
    }

    return rows;
  }, [categories, items, collapsedCategories, projectId]);

  // Map item IDs to row indices (for dependency drawing)
  const itemRowMap = useMemo(() => {
    const map = new Map<number, number>();
    visibleRows.forEach((row, index) => {
      if (row.type === 'item') {
        map.set((row.data as GanttItem).id, index);
      }
    });
    return map;
  }, [visibleRows]);

  // Calculate timeline dimensions
  const days = getDaysBetween(dateRange.start, dateRange.end);
  const config = ZOOM_CONFIG[zoom];
  const timelineWidth = days * config.dayWidth;
  const timelineHeight = HEADER_HEIGHT + visibleRows.length * ROW_HEIGHT;

  // Handlers
  const handleToggleCategory = useCallback((categoryId: number) => {
    setCollapsedCategories(prev => {
      const next = new Set(prev);
      if (next.has(categoryId)) {
        next.delete(categoryId);
      } else {
        next.add(categoryId);
      }
      return next;
    });
  }, []);

  const handleItemClick = useCallback((item: GanttItem) => {
    setSelectedItem(item);
    setIsPanelOpen(true);
  }, []);

  const handleGridClick = useCallback((date: Date, rowIndex: number) => {
    if (!canEdit || !onItemCreate) return;

    // Find which row was clicked
    const row = visibleRows[rowIndex];
    if (!row || row.type === 'category') return; // Can't create on category rows

    // For now, just log. Later: open create modal
    console.log('Grid click:', date, rowIndex, row);
  }, [canEdit, onItemCreate, visibleRows]);

  const handleTodayClick = useCallback(() => {
    if (!timelineRef.current) return;
    
    const today = new Date();
    const daysFromStart = getDaysBetween(dateRange.start, today);
    const scrollPosition = daysFromStart * config.dayWidth - timelineRef.current.clientWidth / 2;
    
    timelineRef.current.scrollTo({
      left: Math.max(0, scrollPosition),
      behavior: 'smooth',
    });
  }, [dateRange, config.dayWidth]);

  const handlePanelClose = useCallback(() => {
    setIsPanelOpen(false);
    setSelectedItem(null);
  }, []);

  const handleItemSave = useCallback(async (updatedItem: Partial<GanttItem>) => {
    if (onItemUpdate) {
      await onItemUpdate(updatedItem);
    }
    setIsPanelOpen(false);
    setSelectedItem(null);
  }, [onItemUpdate]);

  const handleItemDelete = useCallback(async (itemId: number) => {
    if (onItemDelete) {
      await onItemDelete(itemId);
    }
    setIsPanelOpen(false);
    setSelectedItem(null);
  }, [onItemDelete]);

  // Scroll to today on mount
  useEffect(() => {
    const timer = setTimeout(handleTodayClick, 100);
    return () => clearTimeout(timer);
  }, [handleTodayClick]);

  // Render calendar view (placeholder for now)
  if (viewMode === 'calendar') {
    return (
      <div className="kibray-gantt flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <GanttToolbar
          zoom={zoom}
          viewMode={viewMode}
          mode={mode}
          onZoomChange={setZoom}
          onViewModeChange={setViewMode}
          onTodayClick={handleTodayClick}
          onAddClick={canEdit ? () => {} : undefined}
          canEdit={canEdit}
          projectName={projectName}
        />
        <div className="flex-1 flex items-center justify-center text-gray-500">
          <div className="text-center">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-lg font-medium">Calendar View</p>
            <p className="text-sm">Coming in Phase 3</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="kibray-gantt flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden"
    >
      {/* Toolbar */}
      <GanttToolbar
        zoom={zoom}
        viewMode={viewMode}
        mode={mode}
        onZoomChange={setZoom}
        onViewModeChange={setViewMode}
        onTodayClick={handleTodayClick}
        onAddClick={canEdit ? () => {} : undefined}
        canEdit={canEdit}
        projectName={projectName}
      />

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <GanttSidebar
          categories={categories}
          items={items}
          rowHeight={ROW_HEIGHT}
          width={SIDEBAR_WIDTH}
          collapsedCategories={collapsedCategories}
          onToggleCategory={handleToggleCategory}
          onItemClick={handleItemClick}
          canEdit={canEdit}
        />

        {/* Timeline area */}
        <div 
          ref={timelineRef}
          className="flex-1 overflow-auto relative"
        >
          <div 
            className="relative"
            style={{ 
              width: timelineWidth, 
              height: timelineHeight,
              minWidth: '100%',
            }}
          >
            {/* Header */}
            <GanttHeader
              dateRange={dateRange}
              zoom={zoom}
              height={HEADER_HEIGHT}
            />

            {/* Grid */}
            <GanttGrid
              dateRange={dateRange}
              zoom={zoom}
              rowHeight={ROW_HEIGHT}
              rowCount={visibleRows.length}
              headerHeight={HEADER_HEIGHT}
              onClick={handleGridClick}
            />

            {/* Dependency lines */}
            <GanttDependencyLines
              dependencies={dependencies}
              items={items}
              itemRowMap={itemRowMap}
              dateRange={dateRange}
              zoom={zoom}
              rowHeight={ROW_HEIGHT}
              headerHeight={HEADER_HEIGHT}
              width={timelineWidth}
              height={timelineHeight}
            />

            {/* Task bars */}
            {visibleRows.map((row, index) => {
              if (row.type !== 'item') return null;
              const item = row.data as GanttItem;
              
              return (
                <GanttBar
                  key={item.id}
                  item={item}
                  dateRange={dateRange}
                  zoom={zoom}
                  rowHeight={ROW_HEIGHT}
                  rowIndex={index}
                  headerHeight={HEADER_HEIGHT}
                  isSelected={selectedItem?.id === item.id}
                  onClick={handleItemClick}
                  canEdit={canEdit}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* Slide-over panel */}
      <SlideOverPanel
        isOpen={isPanelOpen}
        item={selectedItem}
        categories={categories}
        onClose={handlePanelClose}
        onSave={handleItemSave}
        onDelete={handleItemDelete}
        canEdit={canEdit}
      />
    </div>
  );
};

export default KibrayGantt;
