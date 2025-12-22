// =============================================================================
// Kibray Gantt - Main Component (Phase 2 - Interactive)
// Unified Gantt chart with drag & drop, resize, and click-to-create
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
  ItemStatus,
} from '../types/gantt';
import { useZoom, ZOOM_CONFIG } from '../hooks/useZoom';
import { useDragAndDrop, DragType } from '../hooks/useDragAndDrop';
import { getDaysBetween, addDays, formatDate } from '../utils/dateUtils';

// Components
import { GanttToolbar } from './GanttToolbar';
import { GanttHeader } from './GanttHeader';
import { GanttSidebar } from './GanttSidebar';
import { GanttGrid } from './GanttGrid';
import { GanttBar } from './GanttBarInteractive';
import { GanttDependencyLines } from './GanttDependencyLines';
import { SlideOverPanel } from './SlideOverPanel';
import { CreateItemModal } from './CreateItemModal';
import { CreateTaskModal } from './CreateTaskModal';

// Constants
const SIDEBAR_WIDTH = 280;
const ROW_HEIGHT = 48;
const HEADER_HEIGHT = 80;

export interface KibrayGanttProps {
  mode: GanttMode;
  items: GanttItem[];
  categories: GanttCategory[];
  dependencies: GanttDependency[];
  projectId?: number;
  projectName?: string;
  canEdit?: boolean;
  onItemCreate?: (item: Partial<GanttItem>) => Promise<GanttItem>;
  onItemUpdate?: (item: Partial<GanttItem>) => Promise<void>;
  onItemDelete?: (itemId: number) => Promise<void>;
  onTaskCreate?: (task: { schedule_item_id: number; title: string; description: string; assigned_to: number | null }) => Promise<void>;
  onDependencyCreate?: (dep: Partial<GanttDependency>) => Promise<void>;
  onDependencyDelete?: (depId: number) => Promise<void>;
  initialDateRange?: DateRange;
  initialZoom?: ZoomLevel;
  teamMembers?: { id: number; name: string }[];
}

export const KibrayGantt: React.FC<KibrayGanttProps> = ({
  mode,
  items: initialItems,
  categories,
  dependencies,
  projectId,
  projectName,
  canEdit = false,
  onItemCreate,
  onItemUpdate,
  onItemDelete,
  onTaskCreate,
  onDependencyCreate,
  onDependencyDelete,
  initialDateRange,
  initialZoom = 'WEEK',
  teamMembers = [],
}) => {
  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  // Local items state (for optimistic updates)
  const [items, setItems] = useState<GanttItem[]>(initialItems);
  
  // Sync with prop changes
  useEffect(() => {
    setItems(initialItems);
  }, [initialItems]);

  // State
  const [viewMode, setViewMode] = useState<ViewMode>('gantt');
  const [collapsedCategories, setCollapsedCategories] = useState<Set<number>>(new Set());
  const [selectedItem, setSelectedItem] = useState<GanttItem | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createModalDate, setCreateModalDate] = useState<Date>(new Date());
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [taskModalItem, setTaskModalItem] = useState<GanttItem | null>(null);
  const { zoom, setZoom } = useZoom(initialZoom);

  // Update selectedItem when items change (to reflect new tasks)
  useEffect(() => {
    if (selectedItem) {
      const updatedItem = items.find(i => i.id === selectedItem.id);
      if (updatedItem && updatedItem !== selectedItem) {
        setSelectedItem(updatedItem);
      }
    }
  }, [items, selectedItem]);

  // Calculate date range from items or use default
  const dateRange = useMemo<DateRange>(() => {
    if (initialDateRange) return initialDateRange;

    if (items.length === 0) {
      const today = new Date();
      return {
        start: addDays(today, -15),
        end: addDays(today, 60),
      };
    }

    let minDate = new Date(items[0].start_date);
    let maxDate = new Date(items[0].end_date);

    items.forEach(item => {
      const start = new Date(item.start_date);
      const end = new Date(item.end_date);
      if (start < minDate) minDate = start;
      if (end > maxDate) maxDate = end;
    });

    return {
      start: addDays(minDate, -14),
      end: addDays(maxDate, 21),
    };
  }, [items, initialDateRange]);

  // Drag and drop handler
  const handleDragUpdate = useCallback((item: GanttItem, newStartDate: Date, newEndDate: Date) => {
    // Optimistic update
    setItems(prev => prev.map(i => 
      i.id === item.id 
        ? { ...i, start_date: formatDate(newStartDate), end_date: formatDate(newEndDate) }
        : i
    ));

    // Call API
    if (onItemUpdate) {
      onItemUpdate({
        id: item.id,
        start_date: formatDate(newStartDate),
        end_date: formatDate(newEndDate),
      }).catch(() => {
        // Revert on error
        setItems(prev => prev.map(i => 
          i.id === item.id ? item : i
        ));
      });
    }
  }, [onItemUpdate]);

  const { dragState, handleDragStart, getPreviewDates } = useDragAndDrop({
    zoom,
    dateRangeStart: dateRange.start,
    onItemUpdate: handleDragUpdate,
    enabled: canEdit,
  });

  // Build visible rows
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

  // Map item IDs to row indices
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
    if (!dragState.isDragging) {
      setSelectedItem(item);
      setIsPanelOpen(true);
    }
  }, [dragState.isDragging]);

  const handleGridClick = useCallback((date: Date, rowIndex: number) => {
    if (!canEdit || dragState.isDragging) return;
    
    // Open create modal
    setCreateModalDate(date);
    setIsCreateModalOpen(true);
  }, [canEdit, dragState.isDragging]);

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

  const handleAddClick = useCallback(() => {
    setCreateModalDate(new Date());
    setIsCreateModalOpen(true);
  }, []);

  const handlePanelClose = useCallback(() => {
    setIsPanelOpen(false);
    setSelectedItem(null);
  }, []);

  const handleItemSave = useCallback(async (updatedItem: Partial<GanttItem>) => {
    if (!updatedItem.id) return;

    // Optimistic update
    setItems(prev => prev.map(i => 
      i.id === updatedItem.id ? { ...i, ...updatedItem } : i
    ));

    if (onItemUpdate) {
      try {
        await onItemUpdate(updatedItem);
      } catch (error) {
        // Revert on error - would need original item from selectedItem
        console.error('Failed to update item:', error);
      }
    }
    
    setIsPanelOpen(false);
    setSelectedItem(null);
  }, [onItemUpdate]);

  const handleItemDelete = useCallback(async (itemId: number) => {
    // Optimistic update
    setItems(prev => prev.filter(i => i.id !== itemId));

    if (onItemDelete) {
      try {
        await onItemDelete(itemId);
      } catch (error) {
        // Revert on error
        console.error('Failed to delete item:', error);
      }
    }
    
    setIsPanelOpen(false);
    setSelectedItem(null);
  }, [onItemDelete]);

  const handleCreateItem = useCallback(async (newItem: {
    title: string;
    description: string;
    start_date: string;
    end_date: string;
    status: ItemStatus;
    category_id: number | null;
    is_milestone: boolean;
    is_personal: boolean;
  }) => {
    // Create temporary item for optimistic UI
    const tempItem: GanttItem = {
      id: Date.now(), // Temp ID
      ...newItem,
      project_id: projectId || 0,
      percent_complete: 0,
      order: items.length,
    };

    // Optimistic update
    setItems(prev => [...prev, tempItem]);
    setIsCreateModalOpen(false);

    if (onItemCreate) {
      try {
        const createdItem = await onItemCreate(newItem);
        // Replace temp item with real one
        setItems(prev => prev.map(i => 
          i.id === tempItem.id ? createdItem : i
        ));
      } catch (error) {
        // Revert on error
        setItems(prev => prev.filter(i => i.id !== tempItem.id));
        console.error('Failed to create item:', error);
      }
    }
  }, [projectId, items.length, onItemCreate]);

  // Scroll to today on mount
  useEffect(() => {
    const timer = setTimeout(handleTodayClick, 100);
    return () => clearTimeout(timer);
  }, []);

  // Calendar view placeholder
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
          onAddClick={canEdit ? handleAddClick : undefined}
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
        onAddClick={canEdit ? handleAddClick : undefined}
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
              const isDragging = dragState.isDragging && dragState.item?.id === item.id;
              const previewDates = isDragging ? getPreviewDates() : null;
              
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
                  isDragging={isDragging}
                  previewDates={previewDates}
                  onClick={handleItemClick}
                  onDragStart={handleDragStart}
                  canEdit={canEdit}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* Slide-over panel for editing */}
      <SlideOverPanel
        isOpen={isPanelOpen}
        item={selectedItem}
        categories={categories}
        onClose={handlePanelClose}
        onSave={handleItemSave}
        onDelete={handleItemDelete}
        onCreateTask={(itemId) => {
          // Find the item and open the task modal
          const item = items.find(i => i.id === itemId);
          if (item) {
            setTaskModalItem(item);
            setIsCreateTaskModalOpen(true);
          }
        }}
        canEdit={canEdit}
      />

      {/* Create item modal */}
      <CreateItemModal
        isOpen={isCreateModalOpen}
        initialDate={createModalDate}
        categories={categories}
        onClose={() => setIsCreateModalOpen(false)}
        onCreate={handleCreateItem}
      />

      {/* Create task modal */}
      <CreateTaskModal
        isOpen={isCreateTaskModalOpen}
        item={taskModalItem}
        onClose={() => {
          setIsCreateTaskModalOpen(false);
          setTaskModalItem(null);
        }}
        onCreate={async (task) => {
          if (onTaskCreate) {
            await onTaskCreate(task);
          }
          setIsCreateTaskModalOpen(false);
          setTaskModalItem(null);
        }}
        teamMembers={teamMembers}
      />
    </div>
  );
};

export default KibrayGantt;
