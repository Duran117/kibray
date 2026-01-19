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
import { GanttStageBar } from './GanttStageBar';
import { GanttDependencyLines } from './GanttDependencyLines';
import { SlideOverPanel } from './SlideOverPanel';
import { CreateItemModal } from './CreateItemModal';
import { CreateTaskModal } from './CreateTaskModal';
import { CalendarView } from './CalendarView';

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
  const [localCategories, setLocalCategories] = useState<GanttCategory[]>(categories);
  
  // Sync with prop changes
  useEffect(() => {
    setItems(initialItems);
  }, [initialItems]);

  useEffect(() => {
    setLocalCategories(categories);
  }, [categories]);

  const categoryDateRanges = useMemo(() => {
    console.log('[KibrayGantt] === COMPUTING DATE RANGES ===');
    console.log('[KibrayGantt] localCategories count:', localCategories.length);
    console.log('[KibrayGantt] items count:', items.length);
    
    const itemsByCategory = new Map<number, GanttItem[]>();
    items.forEach(item => {
      if (item.category_id == null) return;
      const list = itemsByCategory.get(item.category_id) || [];
      list.push(item);
      itemsByCategory.set(item.category_id, list);
    });
    
    console.log('[KibrayGantt] itemsByCategory:', Array.from(itemsByCategory.entries()).map(([id, items]) => ({ categoryId: id, itemCount: items.length })));

    const ranges = new Map<number, { start: Date; end: Date }>();
    localCategories.forEach(category => {
      console.log(`[KibrayGantt] Processing category ${category.id} (${category.name}):`, {
        start_date: category.start_date,
        end_date: category.end_date,
        start_date_type: typeof category.start_date,
        end_date_type: typeof category.end_date
      });
      
      if (category.id < 0) return;
      const categoryItems = itemsByCategory.get(category.id) || [];
      let minItemStart: Date | null = null;
      let maxItemEnd: Date | null = null;

      categoryItems.forEach(item => {
        const itemStart = new Date(item.start_date);
        const itemEnd = new Date(item.end_date);
        if (!minItemStart || itemStart < minItemStart) minItemStart = itemStart;
        if (!maxItemEnd || itemEnd > maxItemEnd) maxItemEnd = itemEnd;
      });

      let start = category.start_date ? new Date(category.start_date) : minItemStart;
      let end = category.end_date ? new Date(category.end_date) : maxItemEnd;

      // If stage has no dates and no items, use default range (today + 2 weeks)
      if (!start && !end) {
        const today = new Date();
        start = today;
        end = addDays(today, 14);
        console.log(`[KibrayGantt] Category ${category.id} has no dates, using default range`);
      }

      if (start && !end) end = start;
      if (end && !start) start = end;

      if (start && end) {
        console.log(`[KibrayGantt] Category ${category.id} range:`, { start, end });
        ranges.set(category.id, { start, end });
      } else {
        console.log(`[KibrayGantt] Category ${category.id} has NO range!`);
      }
    });

    console.log('[KibrayGantt] Final ranges:', ranges);
    return ranges;
  }, [localCategories, items]);

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

    const candidateDates: Date[] = [];
    items.forEach(item => {
      candidateDates.push(new Date(item.start_date), new Date(item.end_date));
    });
    categoryDateRanges.forEach(range => {
      candidateDates.push(range.start, range.end);
    });

    if (candidateDates.length === 0) {
      const today = new Date();
      return {
        start: addDays(today, -15),
        end: addDays(today, 60),
      };
    }

    let minDate = candidateDates[0];
    let maxDate = candidateDates[0];
    candidateDates.forEach(date => {
      if (date < minDate) minDate = date;
      if (date > maxDate) maxDate = date;
    });

    return {
      start: addDays(minDate, -14),
      end: addDays(maxDate, 21),
    };
  }, [items, categoryDateRanges, initialDateRange]);

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
    console.log('[KibrayGantt] === COMPUTING VISIBLE ROWS ===');
    console.log('[KibrayGantt] localCategories for rows:', localCategories.map(c => ({ id: c.id, name: c.name })));
    
    const rows: { type: 'category' | 'item'; data: GanttCategory | GanttItem }[] = [];
    
    const sortedCategories = [...localCategories].sort((a, b) => a.order - b.order);
    const orphanItems = items.filter(i => !i.category_id).sort((a, b) => a.order - b.order);

    sortedCategories.forEach(category => {
      rows.push({ type: 'category', data: category });
      console.log(`[KibrayGantt] Added category row: ${category.id} (${category.name})`);

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

    console.log('[KibrayGantt] Total rows:', rows.length);
    console.log('[KibrayGantt] Category rows:', rows.filter(r => r.type === 'category').length);
    return rows;
  }, [localCategories, items, collapsedCategories, projectId]);

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
  // Ensure minimum height for empty grid (at least 10 rows)
  const effectiveRowCount = Math.max(visibleRows.length, 10);
  const timelineHeight = HEADER_HEIGHT + effectiveRowCount * ROW_HEIGHT;

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
    weight_percent: number;
    is_milestone: boolean;
    is_personal: boolean;
  }) => {
    // Create temporary item for optimistic UI
    const tempItem: GanttItem = {
      id: Date.now(), // Temp ID
      ...newItem,
      project_id: projectId || 0,
      percent_complete: 0,
      weight_percent: newItem.weight_percent,
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

  // Calendar view - use real CalendarView component
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
        <div className="flex-1 overflow-hidden">
          <CalendarView
            items={items}
            categories={localCategories}
            onItemClick={handleItemClick}
            onDayClick={(date) => {
              setCreateModalDate(date);
              setIsCreateModalOpen(true);
            }}
            canEdit={canEdit}
          />
        </div>
        
        {/* Slide-over panel for editing from calendar */}
        <SlideOverPanel
          isOpen={isPanelOpen}
          item={selectedItem}
          categories={localCategories}
          onClose={handlePanelClose}
          onSave={handleItemSave}
          onDelete={handleItemDelete}
          onCreateTask={(itemId) => {
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
          categories={localCategories}
          projectId={projectId}
          onClose={() => setIsCreateModalOpen(false)}
          onCreate={handleCreateItem}
          onStageCreated={(category) => {
            setLocalCategories(prev => [...prev, category]);
          }}
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
          categories={localCategories}
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

            {/* Grid - ensure minimum rows for click-to-create even when empty */}
            <GanttGrid
              dateRange={dateRange}
              zoom={zoom}
              rowHeight={ROW_HEIGHT}
              rowCount={Math.max(visibleRows.length, 10)}
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

            {/* Stage bars */}
            {visibleRows.map((row, index) => {
              if (row.type !== 'category') return null;
              const category = row.data as GanttCategory;
              const range = categoryDateRanges.get(category.id);
              console.log(`[Render] Stage ${category.id} (${category.name}) - range:`, range);
              if (!range) {
                console.log(`[Render] Stage ${category.id} has NO range - skipping render`);
                return null;
              }

              return (
                <GanttStageBar
                  key={`stage-${category.id}`}
                  category={category}
                  dateRange={dateRange}
                  zoom={zoom}
                  rowHeight={ROW_HEIGHT}
                  rowIndex={index}
                  headerHeight={HEADER_HEIGHT}
                  startDate={range.start}
                  endDate={range.end}
                />
              );
            })}

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
        categories={localCategories}
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
        categories={localCategories}
        projectId={projectId}
        onClose={() => setIsCreateModalOpen(false)}
        onCreate={handleCreateItem}
        onStageCreated={(category) => {
          console.log('[KibrayGantt] === STAGE CREATED ===');
          console.log('[KibrayGantt] category received:', JSON.stringify(category, null, 2));
          console.log('[KibrayGantt] category.id:', category.id);
          console.log('[KibrayGantt] category.name:', category.name);
          console.log('[KibrayGantt] category.start_date:', category.start_date, '| type:', typeof category.start_date);
          console.log('[KibrayGantt] category.end_date:', category.end_date, '| type:', typeof category.end_date);
          setLocalCategories(prev => {
            console.log('[KibrayGantt] Previous categories count:', prev.length);
            const newCategories = [...prev, category];
            console.log('[KibrayGantt] New categories count:', newCategories.length);
            console.log('[KibrayGantt] All categories:', newCategories.map(c => ({ id: c.id, name: c.name, start: c.start_date, end: c.end_date })));
            return newCategories;
          });
        }}
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
