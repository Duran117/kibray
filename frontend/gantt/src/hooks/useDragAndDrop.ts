// =============================================================================
// Kibray Gantt - useDragAndDrop Hook
// Handles drag to move and resize bars
// =============================================================================

import { useState, useCallback, useRef, useEffect } from 'react';
import { GanttItem, ZoomLevel } from '../types/gantt';
import { ZOOM_CONFIG } from './useZoom';
import { addDays } from '../utils/dateUtils';

export type DragType = 'move' | 'resize-left' | 'resize-right' | null;

interface DragState {
  isDragging: boolean;
  dragType: DragType;
  item: GanttItem | null;
  startX: number;
  startDate: Date;
  endDate: Date;
  currentX: number;
}

interface UseDragAndDropOptions {
  zoom: ZoomLevel;
  dateRangeStart: Date;
  onItemUpdate: (item: GanttItem, newStartDate: Date, newEndDate: Date) => void;
  enabled: boolean;
}

interface UseDragAndDropReturn {
  dragState: DragState;
  handleDragStart: (e: React.MouseEvent, item: GanttItem, type: DragType) => void;
  handleDrag: (e: React.MouseEvent) => void;
  handleDragEnd: () => void;
  getPreviewDates: () => { start: Date; end: Date } | null;
}

const initialDragState: DragState = {
  isDragging: false,
  dragType: null,
  item: null,
  startX: 0,
  startDate: new Date(),
  endDate: new Date(),
  currentX: 0,
};

export function useDragAndDrop(options: UseDragAndDropOptions): UseDragAndDropReturn {
  const { zoom, dateRangeStart, onItemUpdate, enabled } = options;
  const [dragState, setDragState] = useState<DragState>(initialDragState);
  const dragRef = useRef<DragState>(initialDragState);

  const config = ZOOM_CONFIG[zoom];
  const dayWidth = config.dayWidth;

  // Keep ref in sync with state for event handlers
  useEffect(() => {
    dragRef.current = dragState;
  }, [dragState]);

  const handleDragStart = useCallback((
    e: React.MouseEvent,
    item: GanttItem,
    type: DragType
  ) => {
    if (!enabled || !type) return;

    e.preventDefault();
    e.stopPropagation();

    const newState: DragState = {
      isDragging: true,
      dragType: type,
      item,
      startX: e.clientX,
      startDate: new Date(item.start_date),
      endDate: new Date(item.end_date),
      currentX: e.clientX,
    };

    setDragState(newState);
    dragRef.current = newState;

    // Add document listeners
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = type === 'move' ? 'grabbing' : 'ew-resize';
    document.body.style.userSelect = 'none';
  }, [enabled]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!dragRef.current.isDragging) return;

    setDragState(prev => ({
      ...prev,
      currentX: e.clientX,
    }));
  }, []);

  const handleMouseUp = useCallback(() => {
    const state = dragRef.current;
    
    if (state.isDragging && state.item) {
      const preview = calculatePreviewDates(state, dayWidth);
      if (preview) {
        onItemUpdate(state.item, preview.start, preview.end);
      }
    }

    // Reset state
    setDragState(initialDragState);
    dragRef.current = initialDragState;

    // Remove listeners and reset cursor
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, [dayWidth, onItemUpdate, handleMouseMove]);

  const handleDrag = useCallback((e: React.MouseEvent) => {
    if (!dragState.isDragging) return;
    
    setDragState(prev => ({
      ...prev,
      currentX: e.clientX,
    }));
  }, [dragState.isDragging]);

  const handleDragEnd = useCallback(() => {
    handleMouseUp();
  }, [handleMouseUp]);

  const getPreviewDates = useCallback(() => {
    if (!dragState.isDragging || !dragState.item) return null;
    return calculatePreviewDates(dragState, dayWidth);
  }, [dragState, dayWidth]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [handleMouseMove, handleMouseUp]);

  return {
    dragState,
    handleDragStart,
    handleDrag,
    handleDragEnd,
    getPreviewDates,
  };
}

function calculatePreviewDates(
  state: DragState,
  dayWidth: number
): { start: Date; end: Date } | null {
  if (!state.item) return null;

  const deltaX = state.currentX - state.startX;
  const deltaDays = Math.round(deltaX / dayWidth);

  let newStart = new Date(state.startDate);
  let newEnd = new Date(state.endDate);

  switch (state.dragType) {
    case 'move':
      // Move both dates by the same amount
      newStart = addDays(state.startDate, deltaDays);
      newEnd = addDays(state.endDate, deltaDays);
      break;

    case 'resize-left':
      // Only move start date, but don't let it go past end date
      newStart = addDays(state.startDate, deltaDays);
      if (newStart >= newEnd) {
        newStart = addDays(newEnd, -1);
      }
      break;

    case 'resize-right':
      // Only move end date, but don't let it go before start date
      newEnd = addDays(state.endDate, deltaDays);
      if (newEnd <= newStart) {
        newEnd = addDays(newStart, 1);
      }
      break;
  }

  return { start: newStart, end: newEnd };
}

export default useDragAndDrop;
