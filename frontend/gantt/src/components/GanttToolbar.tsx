// =============================================================================
// Kibray Gantt - GanttToolbar Component
// Top toolbar with zoom controls, view toggles, and action buttons
// =============================================================================

import React from 'react';
import { ZoomLevel, ViewMode, GanttMode } from '../types/gantt';

interface GanttToolbarProps {
  zoom: ZoomLevel;
  viewMode: ViewMode;
  mode: GanttMode;
  onZoomChange: (zoom: ZoomLevel) => void;
  onViewModeChange: (mode: ViewMode) => void;
  onTodayClick: () => void;
  onAddClick?: () => void;
  canEdit: boolean;
  projectName?: string;
}

const ZOOM_OPTIONS: { value: ZoomLevel; label: string; icon: string }[] = [
  { value: 'DAY', label: 'Day', icon: 'D' },
  { value: 'WEEK', label: 'Week', icon: 'W' },
  { value: 'MONTH', label: 'Month', icon: 'M' },
  { value: 'QUARTER', label: 'Quarter', icon: 'Q' },
];

export const GanttToolbar: React.FC<GanttToolbarProps> = ({
  zoom,
  viewMode,
  mode,
  onZoomChange,
  onViewModeChange,
  onTodayClick,
  onAddClick,
  canEdit,
  projectName,
}) => {
  const showCalendarToggle = mode === 'pm' || mode === 'master';

  return (
    <div className="gantt-toolbar flex items-center justify-between px-4 py-2 bg-white border-b border-gray-200">
      {/* Left section: Title and context */}
      <div className="flex items-center gap-4">
        {/* Project/Context name */}
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
          </svg>
          <span className="font-semibold text-gray-800">
            {projectName || getModeLabel(mode)}
          </span>
        </div>

        {/* Divider */}
        <div className="h-6 w-px bg-gray-200" />

        {/* View mode toggle (Gantt/Calendar) - only for PM and Master */}
        {showCalendarToggle && (
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            <button
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                viewMode === 'gantt' 
                  ? 'bg-white text-gray-800 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => onViewModeChange('gantt')}
            >
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7" />
                </svg>
                Gantt
              </span>
            </button>
            <button
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                viewMode === 'calendar' 
                  ? 'bg-white text-gray-800 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => onViewModeChange('calendar')}
            >
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Calendar
              </span>
            </button>
          </div>
        )}
      </div>

      {/* Center section: Zoom controls */}
      <div className="flex items-center gap-2">
        {/* Zoom out button */}
        <button
          className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => {
            const idx = ZOOM_OPTIONS.findIndex(z => z.value === zoom);
            if (idx < ZOOM_OPTIONS.length - 1) {
              onZoomChange(ZOOM_OPTIONS[idx + 1].value);
            }
          }}
          disabled={zoom === 'QUARTER'}
          title="Zoom out"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
          </svg>
        </button>

        {/* Zoom level buttons */}
        <div className="flex items-center bg-gray-100 rounded-lg p-1">
          {ZOOM_OPTIONS.map(option => (
            <button
              key={option.value}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                zoom === option.value 
                  ? 'bg-white text-gray-800 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => onZoomChange(option.value)}
              title={option.label}
            >
              {option.icon}
            </button>
          ))}
        </div>

        {/* Zoom in button */}
        <button
          className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => {
            const idx = ZOOM_OPTIONS.findIndex(z => z.value === zoom);
            if (idx > 0) {
              onZoomChange(ZOOM_OPTIONS[idx - 1].value);
            }
          }}
          disabled={zoom === 'DAY'}
          title="Zoom in"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
          </svg>
        </button>
      </div>

      {/* Right section: Actions */}
      <div className="flex items-center gap-2">
        {/* Today button */}
        <button
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          onClick={onTodayClick}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Today
        </button>

        {/* Divider */}
        {canEdit && <div className="h-6 w-px bg-gray-200" />}

        {/* Add button */}
        {canEdit && onAddClick && (
          <button
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm"
            onClick={onAddClick}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Item
          </button>
        )}

        {/* More actions dropdown */}
        <button
          className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
          title="More options"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
          </svg>
        </button>
      </div>
    </div>
  );
};

function getModeLabel(mode: GanttMode): string {
  switch (mode) {
    case 'project':
      return 'Project Schedule';
    case 'master':
      return 'Master Schedule';
    case 'strategic':
      return 'Strategic Planner';
    case 'pm':
      return 'PM Calendar';
    default:
      return 'Gantt View';
  }
}

export default GanttToolbar;
