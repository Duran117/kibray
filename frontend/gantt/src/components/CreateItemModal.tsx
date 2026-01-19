// =============================================================================
// Kibray Gantt - CreateItemModal Component
// Modal for creating new items (groups of activities)
// =============================================================================

import React, { useEffect, useRef, useState } from 'react';
import { getGanttApi } from '../api/ganttApi';
import { GanttCategory, ItemStatus } from '../types/gantt';
import { addDays, formatDate } from '../utils/dateUtils';

interface CreateItemModalProps {
  isOpen: boolean;
  initialDate: Date;
  categories: GanttCategory[];
  projectId?: number;
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
  }) => void | Promise<void>;
  onStageCreated?: (category: GanttCategory) => void;
}

export const CreateItemModal: React.FC<CreateItemModalProps> = ({
  isOpen,
  initialDate,
  categories,
  projectId,
  onClose,
  onCreate,
  onStageCreated,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const titleInputRef = useRef<HTMLInputElement>(null);

  // Item is always a group/bar, milestone is a flag within item
  const [isMilestone, setIsMilestone] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [status] = useState<ItemStatus>('not_started');
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [weightPercent, setWeightPercent] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [localCategories, setLocalCategories] = useState<GanttCategory[]>(categories);
  const [showStageModal, setShowStageModal] = useState(false);
  const [newStageName, setNewStageName] = useState('');
  const [newStageColor, setNewStageColor] = useState('#1F2937');
  const [stageStartDate, setStageStartDate] = useState('');
  const [stageEndDate, setStageEndDate] = useState('');
  const [creatingStage, setCreatingStage] = useState(false);

  const selectedCategory = localCategories.find(cat => cat.id === categoryId) || null;
  const remainingWeight = Math.max(0, selectedCategory?.remaining_weight_percent ?? 100);

  useEffect(() => {
    setLocalCategories(categories);
  }, [categories]);

  useEffect(() => {
    if (categoryId && !localCategories.some(cat => cat.id === categoryId)) {
      setCategoryId(localCategories[0]?.id ?? null);
    }
  }, [localCategories, categoryId]);

  useEffect(() => {
    if (!isOpen) return;

    const start = formatDate(initialDate);
    const end = formatDate(addDays(initialDate, 7));

    setIsMilestone(false);
    setTitle('');
    setDescription('');
    setStartDate(start);
    setEndDate(end);
    setCategoryId(categories.length > 0 ? categories[0].id : null);
    setWeightPercent(0);
    setIsSubmitting(false);
    setShowStageModal(false);
    setNewStageName('');
    setNewStageColor('#1F2937');
    setStageStartDate(start);
    setStageEndDate(end);
    setCreatingStage(false);

    setTimeout(() => titleInputRef.current?.focus(), 100);
  }, [isOpen, initialDate, categories]);

  useEffect(() => {
    if (isMilestone) {
      setEndDate(startDate);
    }
  }, [isMilestone, startDate]);

  useEffect(() => {
    if (!isMilestone && endDate && startDate && endDate < startDate) {
      setEndDate(startDate);
    }
  }, [isMilestone, startDate, endDate]);

  useEffect(() => {
    if (weightPercent > remainingWeight) {
      setWeightPercent(remainingWeight);
    }
  }, [remainingWeight, weightPercent]);

  useEffect(() => {
    if (showStageModal) {
      setStageStartDate(startDate);
      setStageEndDate(endDate);
    }
  }, [showStageModal, startDate, endDate]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

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

    const normalizedEndDate = isMilestone ? startDate : endDate;

    setIsSubmitting(true);
    try {
      await onCreate({
        title: title.trim(),
        description: description.trim(),
        start_date: startDate,
        end_date: normalizedEndDate,
        status,
        category_id: categoryId,
        weight_percent: weightPercent,
        is_milestone: isMilestone,
        is_personal: false,
      });
      onClose();
    } catch (err) {
      alert('Failed to create item.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateStage = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[CreateItemModal] handleCreateStage called');
    console.log('[CreateItemModal] newStageName:', newStageName);
    console.log('[CreateItemModal] projectId:', projectId);
    
    if (!newStageName.trim()) {
      console.log('[CreateItemModal] ERROR: Stage name is empty');
      return;
    }
    if (!projectId) {
      console.log('[CreateItemModal] ERROR: projectId is missing');
      alert('Project ID not available.');
      return;
    }

    setCreatingStage(true);
    try {
      const api = getGanttApi();
      // Use current item dates as default if stage dates not provided
      const effectiveStartDate = stageStartDate || startDate || null;
      const effectiveEndDate = stageEndDate || endDate || null;
      
      console.log('[CreateItemModal] Creating stage with:', {
        projectId,
        name: newStageName.trim(),
        color: newStageColor,
        startDate: effectiveStartDate,
        endDate: effectiveEndDate
      });
      
      const newCat = await api.createCategory({
        project_id: projectId,
        name: newStageName.trim(),
        color: newStageColor,
        start_date: effectiveStartDate,
        end_date: effectiveEndDate,
      });
      
      console.log('[CreateItemModal] Stage created successfully:', newCat);
      console.log('[CreateItemModal] newCat.start_date:', newCat.start_date);
      console.log('[CreateItemModal] newCat.end_date:', newCat.end_date);
      
      setLocalCategories(prev => [...prev, newCat]);
      setCategoryId(newCat.id);
      setShowStageModal(false);
      
      console.log('[CreateItemModal] Calling onStageCreated callback...');
      onStageCreated?.(newCat);
      console.log('[CreateItemModal] onStageCreated callback completed');
    } catch (err: any) {
      console.error('[CreateItemModal] Failed to create stage:', err);
      console.error('[CreateItemModal] Error details:', err.message);
      alert(`Failed to create stage: ${err.message}`);
    } finally {
      setCreatingStage(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 z-50" />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          ref={modalRef}
          className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden"
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Create Item</h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  Start: <span className="font-medium text-gray-700">{formatDate(initialDate, 'full')}</span>
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  min={startDate}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                  disabled={isMilestone}
                />
              </div>
            </div>

            {/* Milestone toggle */}
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isMilestone}
                  onChange={(e) => setIsMilestone(e.target.checked)}
                  className="w-4 h-4 text-violet-600 border-gray-300 rounded focus:ring-violet-500"
                />
                <span className="text-sm font-medium text-gray-700">🎯 Mark as Milestone</span>
              </label>
            </div>

            {/* Category (Stage) */}
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
                  setWeightPercent(0);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {localCategories.length === 0 && <option value="">No stages yet</option>}
                {localCategories.map(cat => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name} ({cat.remaining_weight_percent ?? 100}% available)
                  </option>
                ))}
                <option value="__create__">+ Create new Stage...</option>
              </select>
            </div>

            {/* Stage Creation Modal */}
            {showStageModal && (
              <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40">
                <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm p-6 relative">
                  <button
                    onClick={() => setShowStageModal(false)}
                    className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                  <h3 className="text-lg font-semibold mb-3 text-gray-800">Create New Stage</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Stages group related items (e.g., "Interior Painting", "Flooring")
                  </p>
                  <form onSubmit={handleCreateStage} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Stage Name *</label>
                      <input
                        type="text"
                        value={newStageName}
                        onChange={e => setNewStageName(e.target.value)}
                        placeholder="e.g., Interior Painting"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        required
                        autoFocus
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                      <div className="flex items-center gap-3">
                        <input
                          type="color"
                          value={newStageColor}
                          onChange={e => setNewStageColor(e.target.value)}
                          className="w-12 h-10 p-1 border border-gray-300 rounded-lg cursor-pointer"
                        />
                        <span className="text-sm text-gray-500">{newStageColor}</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                        <input
                          type="date"
                          value={stageStartDate}
                          onChange={e => setStageStartDate(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                        <input
                          type="date"
                          value={stageEndDate}
                          onChange={e => setStageEndDate(e.target.value)}
                          min={stageStartDate}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end gap-2 pt-2">
                      <button
                        type="button"
                        onClick={() => setShowStageModal(false)}
                        className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg"
                        disabled={creatingStage}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          console.log('[CreateStageBtn] Button clicked!');
                          handleCreateStage(e as any);
                        }}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
                        disabled={!newStageName.trim() || creatingStage}
                      >
                        {creatingStage ? 'Creating...' : 'Create Stage'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* Weight Percent */}
            {categoryId && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Weight in Stage (%)
                  <span className="ml-2 text-xs text-gray-500">Max: {remainingWeight}%</span>
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
