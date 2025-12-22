// =============================================================================
// Kibray Gantt - SlideOverPanel Component
// Right slide-over panel for editing items (Monday.com style)
// =============================================================================

import React, { useEffect, useRef } from 'react';
import { GanttItem, GanttCategory, ItemStatus } from '../types/gantt';
import { getBarColor, getStatusLabel } from '../utils/colorUtils';
import { formatDate } from '../utils/dateUtils';

interface SlideOverPanelProps {
  isOpen: boolean;
  item: GanttItem | null;
  categories: GanttCategory[];
  onClose: () => void;
  onSave: (item: Partial<GanttItem>) => void;
  onDelete: (itemId: number) => void;
  onCreateTask?: (itemId: number) => void;
  canEdit: boolean;
}

const STATUS_OPTIONS: { value: ItemStatus; label: string; color: string }[] = [
  { value: 'not_started', label: 'Not Started', color: '#9ca3af' },
  { value: 'in_progress', label: 'In Progress', color: '#3b82f6' },
  { value: 'completed', label: 'Completed', color: '#22c55e' },
  { value: 'blocked', label: 'Blocked', color: '#ef4444' },
  { value: 'on_hold', label: 'On Hold', color: '#f59e0b' },
];

export const SlideOverPanel: React.FC<SlideOverPanelProps> = ({
  isOpen,
  item,
  categories,
  onClose,
  onSave,
  onDelete,
  onCreateTask,
  canEdit,
}) => {
  const panelRef = useRef<HTMLDivElement>(null);
  const [formData, setFormData] = React.useState<Partial<GanttItem>>({});
  const [isDirty, setIsDirty] = React.useState(false);

  // Initialize form data when item changes
  useEffect(() => {
    if (item) {
      setFormData({
        title: item.title,
        description: item.description,
        start_date: item.start_date,
        end_date: item.end_date,
        status: item.status,
        percent_complete: item.percent_complete,
        category_id: item.category_id,
        is_milestone: item.is_milestone,
        is_personal: item.is_personal,
        assigned_to: item.assigned_to,
      });
      setIsDirty(false);
    }
  }, [item]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      // Delay adding listener to prevent immediate close
      setTimeout(() => {
        document.addEventListener('mousedown', handleClickOutside);
      }, 100);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  const handleChange = (field: keyof GanttItem, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setIsDirty(true);
  };

  const handleSave = () => {
    if (item && isDirty) {
      onSave({ id: item.id, ...formData });
      setIsDirty(false);
    }
  };

  const handleDelete = () => {
    if (item && confirm('Are you sure you want to delete this item?')) {
      onDelete(item.id);
      onClose();
    }
  };

  if (!item) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className={`fixed inset-0 bg-black/20 z-40 transition-opacity ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className={`fixed top-0 right-0 h-full w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-out flex flex-col ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{ maxHeight: '100vh' }}
      >
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-3">
            {/* Status color indicator */}
            <div 
              className={`w-3 h-3 rounded-sm ${item.is_milestone ? 'rotate-45' : ''}`}
              style={{ backgroundColor: getBarColor(item.status, item.is_milestone, item.is_personal) }}
            />
            <span className="font-semibold text-gray-800">Edit Item</span>
          </div>
          
          <button
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded transition-colors"
            onClick={onClose}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title
            </label>
            <input
              type="text"
              value={formData.title || ''}
              onChange={(e) => handleChange('title', e.target.value)}
              disabled={!canEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="Enter title..."
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => handleChange('description', e.target.value)}
              disabled={!canEdit}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
              placeholder="Add a description..."
            />
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={formData.start_date?.split('T')[0] || ''}
                onChange={(e) => handleChange('start_date', e.target.value)}
                disabled={!canEdit}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={formData.end_date?.split('T')[0] || ''}
                onChange={(e) => handleChange('end_date', e.target.value)}
                disabled={!canEdit}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map(status => (
                <button
                  key={status.value}
                  onClick={() => canEdit && handleChange('status', status.value)}
                  disabled={!canEdit}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                    formData.status === status.value
                      ? 'ring-2 ring-offset-1 shadow-sm'
                      : 'opacity-60 hover:opacity-100'
                  } disabled:cursor-not-allowed`}
                  style={{ 
                    backgroundColor: `${status.color}20`,
                    color: status.color,
                    ['--tw-ring-color' as string]: status.color,
                  }}
                >
                  <div 
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: status.color }}
                  />
                  {status.label}
                </button>
              ))}
            </div>
          </div>

          {/* Progress */}
          {!formData.is_milestone && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Progress: {formData.percent_complete || 0}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={formData.percent_complete || 0}
                onChange={(e) => handleChange('percent_complete', parseInt(e.target.value))}
                disabled={!canEdit}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:cursor-not-allowed accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>
          )}

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={formData.category_id || ''}
              onChange={(e) => handleChange('category_id', e.target.value ? parseInt(e.target.value) : null)}
              disabled={!canEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">No category</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          {/* Toggles */}
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_milestone || false}
                onChange={(e) => handleChange('is_milestone', e.target.checked)}
                disabled={!canEdit}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:cursor-not-allowed"
              />
              <span className="text-sm text-gray-700">
                Mark as milestone
              </span>
            </label>
            
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_personal || false}
                onChange={(e) => handleChange('is_personal', e.target.checked)}
                disabled={!canEdit}
                className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500 disabled:cursor-not-allowed"
              />
              <span className="text-sm text-gray-700">
                Personal task (private)
              </span>
            </label>
          </div>

          {/* Tasks Section */}
          {!formData.is_milestone && (
            <div className="pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  Tasks ({item.tasks?.length || 0})
                </label>
                {canEdit && onCreateTask && (
                  <button
                    onClick={() => onCreateTask(item.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add Task
                  </button>
                )}
              </div>
              
              {/* Task List */}
              {item.tasks && item.tasks.length > 0 ? (
                <div className="space-y-2">
                  {item.tasks.map(task => (
                    <div 
                      key={task.id}
                      className={`flex items-center gap-3 p-2 rounded-lg border ${
                        task.is_completed 
                          ? 'bg-green-50 border-green-200' 
                          : 'bg-gray-50 border-gray-200'
                      }`}
                    >
                      <div className={`w-2 h-2 rounded-full ${
                        task.is_completed ? 'bg-green-500' : 'bg-gray-400'
                      }`} />
                      <span className={`flex-1 text-sm ${
                        task.is_completed ? 'text-gray-500 line-through' : 'text-gray-700'
                      }`}>
                        {task.title}
                      </span>
                      {task.assigned_to_name && (
                        <span className="text-xs text-gray-400">
                          {task.assigned_to_name}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-400 text-sm">
                  <svg className="w-8 h-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  No tasks yet
                  {canEdit && onCreateTask && (
                    <p className="mt-1">Click "Add Task" to create one</p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Meta info */}
          <div className="pt-4 border-t border-gray-200 text-xs text-gray-400 space-y-1">
            <p>Created: {formatDate(new Date(item.created_at || ''), 'full')}</p>
            {item.updated_at && (
              <p>Updated: {formatDate(new Date(item.updated_at), 'full')}</p>
            )}
            {item.assigned_to && (
              <p>Assigned to: {item.assigned_to}</p>
            )}
          </div>
        </div>

        {/* Footer */}
        {canEdit && (
          <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
            <button
              onClick={handleDelete}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete
            </button>

            <div className="flex items-center gap-2">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!isDirty}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save Changes
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default SlideOverPanel;
