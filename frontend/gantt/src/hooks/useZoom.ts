// =============================================================================
// Kibray Gantt - useZoom Hook
// Manages zoom level state and configuration
// =============================================================================

import { useState, useCallback } from 'react';
import { ZoomLevel } from '../types/gantt';

export interface ZoomConfig {
  dayWidth: number;
  headerFormat: 'day' | 'week' | 'month';
  showWeekends: boolean;
}

export const ZOOM_CONFIG: Record<ZoomLevel, ZoomConfig> = {
  DAY: {
    dayWidth: 48,
    headerFormat: 'day',
    showWeekends: true,
  },
  WEEK: {
    dayWidth: 32,
    headerFormat: 'week',
    showWeekends: true,
  },
  MONTH: {
    dayWidth: 12,
    headerFormat: 'month',
    showWeekends: false,
  },
  QUARTER: {
    dayWidth: 4,
    headerFormat: 'month',
    showWeekends: false,
  },
};

const ZOOM_ORDER: ZoomLevel[] = ['DAY', 'WEEK', 'MONTH', 'QUARTER'];

interface UseZoomReturn {
  zoom: ZoomLevel;
  setZoom: (zoom: ZoomLevel) => void;
  config: ZoomConfig;
  zoomIn: () => void;
  zoomOut: () => void;
  canZoomIn: boolean;
  canZoomOut: boolean;
}

export function useZoom(defaultZoom: ZoomLevel = 'WEEK'): UseZoomReturn {
  const [zoom, setZoom] = useState<ZoomLevel>(defaultZoom);
  
  const config = ZOOM_CONFIG[zoom];
  
  const currentIndex = ZOOM_ORDER.indexOf(zoom);
  const canZoomIn = currentIndex > 0;
  const canZoomOut = currentIndex < ZOOM_ORDER.length - 1;
  
  const zoomIn = useCallback(() => {
    if (canZoomIn) {
      setZoom(ZOOM_ORDER[currentIndex - 1]);
    }
  }, [currentIndex, canZoomIn]);
  
  const zoomOut = useCallback(() => {
    if (canZoomOut) {
      setZoom(ZOOM_ORDER[currentIndex + 1]);
    }
  }, [currentIndex, canZoomOut]);
  
  return {
    zoom,
    setZoom,
    config,
    zoomIn,
    zoomOut,
    canZoomIn,
    canZoomOut,
  };
}

export default useZoom;