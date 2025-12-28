// =============================================================================
// Kibray Gantt - CreateItemModal Component
// Modal for creating new items on click-to-create
// =============================================================================

import React, { useState, useEffect, useRef } from 'react';
import { getGanttApi } from '../api/ganttApi';
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
    weight_percent: number;
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
  const [weightPercent, setWeightPercent] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showStageModal, setShowStageModal] = useState(false);
  const [newStageName, setNewStageName] = useState('');
  const [newStageColor, setNewStageColor] = useState('#1F2937');
  const [creatingStage, setCreatingStage] = useState(false);

  // Get selected category info
  const selectedCategory = categories.find(c => c.id === categoryId);
  const remainingWeight = selectedCategory?.remaining_weight_percent ?? 100;

  // Local categories state for dynamic add
  const [localCategories, setLocalCategories] = useState(categories);
  useEffect(() => { setLocalCategories(categories); }, [categories]);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setItemType('task');
      setTitle('');
      setDescription('');
      setStartDate(formatDate(initialDate));
      setEndDate(formatDate(new Date(initialDate.getTime() + 7 * 24 * 60 * 60 * 1000)));
  setCategoryId(categories.length > 0 ? categories[0].id : null);
      setWeightPercent(0);
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={e => setEndDate(e.target.value)}
                  min={startDate}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    // Validate weight doesn't exceed remaining
    if (weightPercent > remainingWeight) {
      alert(`Weight cannot exceed ${remainingWeight}% available in this stage`);
      return;
    }

    setIsSubmitting(true);

    onCreate({
      title: title.trim(),
      description: description.trim(),
      start_date: startDate,
      end_date: itemType === 'milestone' ? startDate : endDate,
      status: 'not_started',
      category_id: categoryId,
      weight_percent: weightPercent,
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

            {/* Category (Stage) */}
            {itemType !== 'personal' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stage
                  {selectedCategory && (
                    <span className="ml-2 text-xs text-gray-500">
                      ({selectedCategory.calculated_progress || 0}% complete)
                    </span>
                  )}
                </label>
                <select
                  value={categoryId || ''}
                  onChange={(e) => {
                    if (e.target.value === '__create__') {
                      setShowStageModal(true);
                      setNewStageName('');
                      setNewStageColor('#1F2937');
                      return;
                    }
                    setCategoryId(e.target.value ? parseInt(e.target.value) : null);
                    setWeightPercent(0); // Reset weight when changing stage
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {localCategories.length === 0 && <option value="">No stages yet</option>}
                  {localCategories.map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name} ({cat.remaining_weight_percent ?? 100}% available)
                    </option>
                  ))}
                  <option value="__create__">➕ Create new Stage…</option>
                </select>
              </div>
            )}
      {/* Stage Creation Modal */}
      {showStageModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-xs p-6 relative">
            <button
              onClick={() => setShowStageModal(false)}
              className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <h3 className="text-lg font-semibold mb-3 text-gray-800">Create New Stage</h3>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (!newStageName.trim()) return;
                setCreatingStage(true);
                try {
                  const api = getGanttApi();
                  const newCat = await api.createCategory({ name: newStageName.trim(), color: newStageColor });
                  setLocalCategories((prev) => [...prev, newCat]);
                  setCategoryId(newCat.id);
                  setShowStageModal(false);
                } catch (err) {
                  alert('Failed to create stage.');
                } finally {
                  setCreatingStage(false);
                }
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stage Name *</label>
                <input
                  type="text"
                  value={newStageName}
                  onChange={e => setNewStageName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                <input
                  type="color"
                  value={newStageColor}
                  onChange={e => setNewStageColor(e.target.value)}
                  className="w-12 h-8 p-0 border-0 bg-transparent"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowStageModal(false)}
                  className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg"
                  disabled={creatingStage}
                >Cancel</button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
                  disabled={!newStageName.trim() || creatingStage}
                >{creatingStage ? 'Creating…' : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

            {/* Weight Percent */}
            {itemType !== 'personal' && categoryId && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Weight in Stage (%)
                  <span className="ml-2 text-xs text-gray-500">
                    Max: {remainingWeight}%
                  </span>
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="0"
                    max={remainingWeight}
                    step="1"
                    value={weightPercent}
                    onChange={(e) => setWeightPercent(parseFloat(e.target.value))}
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <input
                    type="number"
                    min="0"
                    max={remainingWeight}
                    step="0.5"
                    value={weightPercent}
                    onChange={(e) => setWeightPercent(Math.min(parseFloat(e.target.value) || 0, remainingWeight))}
                    className="w-20 px-2 py-1 border border-gray-300 rounded-lg text-center text-sm"
                  />
                  <span className="text-sm text-gray-500">%</span>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  This determines how much this item contributes to the stage progress
                </p>
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
