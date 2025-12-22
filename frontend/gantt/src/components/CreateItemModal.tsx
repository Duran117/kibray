// =============================================================================
// Kibray Gantt - CreateItemModal Component
// Modal for creating new items on click-to-create
// =============================================================================

import React, { useState, useEffect, useRef } from 'react';
import { GanttCategory, ItemStatus } from '../types/gantt';
import { formatDate } from '../utils/dateUtils';

interface CreateItemModalProps {
  isOpen: boolean;
  initialDate: Date;
  categories: GanttCategory[];
  onClose: () => void;
  onCreate: (item: {
    title: string;
    description: string;
    start_date: string;
    end_date: string;
    status: ItemStatus;
    category_id: number | null;
    is_milestone: boolean;
    is_personal: boolean;
  }) => void;
}

type ItemType = 'task' | 'milestone' | 'personal';

export const CreateItemModal: React.FC<CreateItemModalProps> = ({
  isOpen,
  initialDate,
  categories,
  onClose,
  onCreate,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const titleInputRef = useRef<HTMLInputElement>(null);

  const [itemType, setItemType] = useState<ItemType>('task');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState(formatDate(initialDate));
  const [endDate, setEndDate] = useState(formatDate(new Date(initialDate.getTime() + 7 * 24 * 60 * 60 * 1000)));
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setItemType('task');
      setTitle('');
      setDescription('');
      setStartDate(formatDate(initialDate));
      setEndDate(formatDate(new Date(initialDate.getTime() + 7 * 24 * 60 * 60 * 1000)));
      setCategoryId(categories.length > 0 ? categories[0].id : null);
      setIsSubmitting(false);

      // Focus title input
      setTimeout(() => titleInputRef.current?.focus(), 100);
    }
  }, [isOpen, initialDate, categories]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      setTimeout(() => document.addEventListener('mousedown', handleClickOutside), 100);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);

    onCreate({
      title: title.trim(),
      description: description.trim(),
      start_date: startDate,
      end_date: itemType === 'milestone' ? startDate : endDate,
      status: 'not_started',
      category_id: categoryId,
      is_milestone: itemType === 'milestone',
      is_personal: itemType === 'personal',
    });
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30 z-40" />

      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div
          ref={modalRef}
          className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-semibold text-gray-800">Create New Item</h2>
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-5 space-y-5">
            {/* Item type selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
              <div className="flex gap-2">
                {[
                  { value: 'task', label: 'Task', icon: '📋', color: 'blue' },
                  { value: 'milestone', label: 'Milestone', icon: '🎯', color: 'violet' },
                  { value: 'personal', label: 'Personal', icon: '👤', color: 'amber' },
                ].map(type => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setItemType(type.value as ItemType)}
                    className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border-2 transition-all ${
                      itemType === type.value
                        ? `border-${type.color}-500 bg-${type.color}-50 text-${type.color}-700`
                        : 'border-gray-200 text-gray-600 hover:border-gray-300'
                    }`}
                    style={{
                      borderColor: itemType === type.value ? 
                        (type.color === 'blue' ? '#3b82f6' : type.color === 'violet' ? '#8b5cf6' : '#f59e0b') : undefined,
                      backgroundColor: itemType === type.value ?
                        (type.color === 'blue' ? '#eff6ff' : type.color === 'violet' ? '#f5f3ff' : '#fffbeb') : undefined,
                    }}
                  >
                    <span>{type.icon}</span>
                    <span className="text-sm font-medium">{type.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
              <input
                ref={titleInputRef}
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter item title..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add a description..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              />
            </div>

            {/* Dates */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {itemType === 'milestone' ? 'Date' : 'Start Date'}
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              {itemType !== 'milestone' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    min={startDate}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              )}
            </div>

            {/* Category */}
            {itemType !== 'personal' && categories.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={categoryId || ''}
                  onChange={(e) => setCategoryId(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">No category</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!title.trim() || isSubmitting}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating...' : 'Create Item'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
};

export default CreateItemModal;
