// =============================================================================
// Kibray Gantt - CreateItemModal Component
// Modal for creating new items (groups of activities)
// =============================================================================

import React, { useEffect, useRef, useState } from 'react';
import { getGanttApi } from '../api/ganttApi';
import { GanttCategory, GanttMode, ItemStatus } from '../types/gantt';
import { addDays, formatDate } from '../utils/dateUtils';

interface CreateItemModalProps {
  isOpen: boolean;
  initialDate: Date;
  categories: GanttCategory[];
  projectId?: number;
  mode?: GanttMode;
  onClose: () => void;
  onCreate: (item: {
    title: string;
    description: string;
    start_date: string;
    end_date: string;
    status: ItemStatus;
    category_id: number | null;
    project_id?: number;
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
  mode = 'project',
  onClose,
  onCreate,
  onStageCreated,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const titleInputRef = useRef<HTMLInputElement>(null);

  // Item is always a group/bar, milestone is a flag within item
  const [isMilestone, setIsMilestone] = useState(false);
  const [isPersonal, setIsPersonal] = useState(false);
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

  // Master-mode: categories prop are projects; stages are loaded per-project
  const isMasterMode = mode === 'master';
  const [selectedMasterProjectId, setSelectedMasterProjectId] = useState<number | null>(null);
  const [projectStages, setProjectStages] = useState<GanttCategory[]>([]);
  const [loadingStages, setLoadingStages] = useState(false);

  // In master mode use projectStages; in project mode use localCategories
  const stageList = isMasterMode ? projectStages : localCategories;
  const selectedCategory = stageList.find(cat => cat.id === categoryId) || null;
  const remainingWeight = Math.max(0, selectedCategory?.remaining_weight_percent ?? 100);
  // Effective project id for stage creation
  const effectiveProjectId = isMasterMode ? selectedMasterProjectId : projectId;

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
    setIsPersonal(false);
    setTitle('');
    setDescription('');
    setStartDate(start);
    setEndDate(end);
    setCategoryId(isMasterMode ? null : (categories.length > 0 ? categories[0].id : null));
    setWeightPercent(0);
    setIsSubmitting(false);
    setShowStageModal(false);
    setNewStageName('');
    setNewStageColor('#1F2937');
    setStageStartDate(start);
    setStageEndDate(end);
    setCreatingStage(false);
    if (isMasterMode) {
      setSelectedMasterProjectId(null);
      setProjectStages([]);
    }

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

  // Master mode: load real stages when a project is selected
  useEffect(() => {
    if (!isMasterMode || !selectedMasterProjectId) {
      setProjectStages([]);
      setCategoryId(null);
      return;
    }
    let cancelled = false;
    setLoadingStages(true);
    const api = getGanttApi();
    api.fetchGanttData('project', { projectId: selectedMasterProjectId })
      .then((data: any) => {
        if (cancelled) return;
        const phases = (data.phases || []).map((p: any) => ({
          id: p.id,
          name: p.name,
          color: p.color,
          order: p.order,
          is_collapsed: false,
          project_id: p.project,
          start_date: p.start_date,
          end_date: p.end_date,
          weight_percent: p.weight_percent,
          calculated_progress: p.calculated_progress,
          remaining_weight_percent: p.remaining_weight_percent,
        }));
        setProjectStages(phases);
        setCategoryId(phases.length > 0 ? phases[0].id : null);
      })
      .catch(() => { if (!cancelled) setProjectStages([]); })
      .finally(() => { if (!cancelled) setLoadingStages(false); });
    return () => { cancelled = true; };
  }, [isMasterMode, selectedMasterProjectId]);

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
    if (isMasterMode && !isPersonal && !selectedMasterProjectId) return;

    const normalizedEndDate = isMilestone ? startDate : endDate;

    setIsSubmitting(true);
    try {
      await onCreate({
        title: title.trim(),
        description: description.trim(),
        start_date: startDate,
        end_date: normalizedEndDate,
        status,
        category_id: isPersonal ? null : categoryId,
        project_id: isMasterMode ? (selectedMasterProjectId || undefined) : undefined,
        weight_percent: isPersonal ? 0 : weightPercent,
        is_milestone: isMilestone,
        is_personal: isPersonal,
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
    
    if (!newStageName.trim()) return;
    if (!effectiveProjectId) {
      alert('Please select a project first.');
      return;
    }

    setCreatingStage(true);
    try {
      const api = getGanttApi();
      // Use current item dates as default if stage dates not provided
      const effectiveStartDate = stageStartDate || startDate || null;
      const effectiveEndDate = stageEndDate || endDate || null;
      
      const newCat = await api.createCategory({
        project_id: effectiveProjectId,
        name: newStageName.trim(),
        color: newStageColor,
        start_date: effectiveStartDate,
        end_date: effectiveEndDate,
      });
      
      if (isMasterMode) {
        setProjectStages(prev => [...prev, newCat]);
      } else {
        setLocalCategories(prev => [...prev, newCat]);
      }
      setCategoryId(newCat.id);
      setShowStageModal(false);
      onStageCreated?.(newCat);
    } catch (err: any) {
      console.error('Failed to create stage:', err);
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

            {/* Master mode: Personal toggle + Project selector */}
            {isMasterMode && (
              <>
                {/* Personal event toggle */}
                <div className="flex items-center gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <label className="flex items-center gap-2 cursor-pointer flex-1">
                    <input
                      type="checkbox"
                      checked={isPersonal}
                      onChange={(e) => {
                        setIsPersonal(e.target.checked);
                        if (e.target.checked) {
                          setSelectedMasterProjectId(null);
                          setCategoryId(null);
                        }
                      }}
                      className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                    />
                    <div>
                      <span className="text-sm font-medium text-gray-700">🔒 Personal / Office Event</span>
                      <p className="text-xs text-gray-500">Not visible to clients (meetings, internal tasks, etc.)</p>
                    </div>
                  </label>
                </div>

                {/* Project selector (hidden when personal) */}
                {!isPersonal && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Project *</label>
                    <select
                      value={selectedMasterProjectId || ''}
                      onChange={(e) => setSelectedMasterProjectId(e.target.value ? parseInt(e.target.value) : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    >
                      <option value="">Select a project...</option>
                      {categories.map(cat => (
                        <option key={cat.id} value={cat.project_id || cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </>
            )}

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

            {/* Category (Stage) — hide when personal event */}
            {!(isMasterMode && isPersonal) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stage
                {selectedCategory && (
                  <span className="ml-2 text-xs text-gray-500">
                    ({selectedCategory.calculated_progress || 0}% complete)
                  </span>
                )}
              </label>
              {loadingStages ? (
                <div className="flex items-center gap-2 text-sm text-gray-500 py-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  Loading stages...
                </div>
              ) : (
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
                {stageList.length === 0 && <option value="">No stages yet</option>}
                {stageList.map(cat => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name} ({cat.remaining_weight_percent ?? 100}% available)
                  </option>
                ))}
                {effectiveProjectId && <option value="__create__">+ Create new Stage...</option>}
              </select>
              )}
            </div>
            )}

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
                        onClick={handleCreateStage}
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
                disabled={!title.trim() || isSubmitting || (isMasterMode && !isPersonal && !selectedMasterProjectId)}
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
