// =============================================================================
// Kibray Gantt - GanttSidebar Component
// Left sidebar with category/item labels (collapsible hierarchy)
// =============================================================================

import React from 'react';
import { GanttCategory, GanttItem } from '../types/gantt';
import { getBarColor, getStatusLabel } from '../utils/colorUtils';

interface SidebarRow {
  type: 'category' | 'item';
  data: GanttCategory | GanttItem;
  depth: number;
  isCollapsed?: boolean;
  isHidden?: boolean;
}

interface GanttSidebarProps {
  categories: GanttCategory[];
  items: GanttItem[];
  rowHeight: number;
  width: number;
  collapsedCategories: Set<number>;
  onToggleCategory: (categoryId: number) => void;
  onItemClick: (item: GanttItem) => void;
  canEdit: boolean;
}

export const GanttSidebar: React.FC<GanttSidebarProps> = ({
  categories,
  items,
  rowHeight,
  width,
  collapsedCategories,
  onToggleCategory,
  onItemClick,
  canEdit,
}) => {
  // Build flat list of rows respecting hierarchy and collapse state
  const rows: SidebarRow[] = React.useMemo(() => {
    const result: SidebarRow[] = [];
    
    // Sort categories by order
    const sortedCategories = [...categories].sort((a, b) => a.order - b.order);
    
    // Items without category
    const orphanItems = items
      .filter(item => !item.category_id)
      .sort((a, b) => a.order - b.order);

    // Add categories and their items
    sortedCategories.forEach(category => {
      const isCollapsed = collapsedCategories.has(category.id);
      
      result.push({
        type: 'category',
        data: category,
        depth: 0,
        isCollapsed,
      });

      // Add items under this category if not collapsed
      if (!isCollapsed) {
        const categoryItems = items
          .filter(item => item.category_id === category.id)
          .sort((a, b) => a.order - b.order);

        categoryItems.forEach(item => {
          result.push({
            type: 'item',
            data: item,
            depth: 1,
          });
        });
      }
    });

    // Add orphan items at the end
    if (orphanItems.length > 0) {
      result.push({
        type: 'category',
        data: { 
          id: -1, 
          name: 'Uncategorized', 
          color: '#6b7280', 
          order: 9999, 
          is_collapsed: false,
          project_id: 0 
        } as GanttCategory,
        depth: 0,
        isCollapsed: false,
      });

      orphanItems.forEach(item => {
        result.push({
          type: 'item',
          data: item,
          depth: 1,
        });
      });
    }

    return result;
  }, [categories, items, collapsedCategories]);

  return (
    <div 
      className="gantt-sidebar bg-white border-r border-gray-200 overflow-y-auto overflow-x-hidden flex-shrink-0"
      style={{ width }}
    >
      {/* Header */}
      <div 
        className="sticky top-0 z-10 bg-gray-50 border-b border-gray-200 px-4 flex items-center font-semibold text-sm text-gray-700"
        style={{ height: 80 }} // Match header height
      >
        <span className="flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
          Tasks
        </span>
      </div>

      {/* Rows */}
      {rows.map((row, index) => {
        if (row.type === 'category') {
          const category = row.data as GanttCategory;
          const isCollapsed = row.isCollapsed;
          
          return (
            <div
              key={`cat-${category.id}`}
              className="flex items-center gap-2 px-3 border-b border-gray-100 bg-gray-50 hover:bg-gray-100 cursor-pointer select-none transition-colors"
              style={{ height: rowHeight }}
              onClick={() => category.id !== -1 && onToggleCategory(category.id)}
            >
              {/* Collapse toggle */}
              {category.id !== -1 && (
                <button className="p-1 hover:bg-gray-200 rounded transition-colors">
                  <svg 
                    className={`w-4 h-4 text-gray-500 transition-transform ${isCollapsed ? '-rotate-90' : ''}`}
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              )}
              
              {/* Color indicator */}
              <div 
                className="w-3 h-3 rounded-sm flex-shrink-0"
                style={{ backgroundColor: category.color }}
              />
              
              {/* Category name */}
              <span className="font-semibold text-sm text-gray-800 truncate">
                {category.name}
              </span>
              
              {/* Item count */}
              <span className="ml-auto text-xs text-gray-400">
                {items.filter(i => i.category_id === category.id).length}
              </span>
            </div>
          );
        }

        // Item row
        const item = row.data as GanttItem;
        const statusColor = getBarColor(item.status, item.is_milestone, item.is_personal);
        
        return (
          <div
            key={`item-${item.id}`}
            className="flex items-center gap-2 px-3 border-b border-gray-50 hover:bg-blue-50 cursor-pointer select-none transition-colors group"
            style={{ 
              height: rowHeight,
              paddingLeft: `${row.depth * 16 + 12}px`
            }}
            onClick={() => onItemClick(item)}
          >
            {/* Status indicator */}
            <div 
              className={`w-2 h-2 rounded-full flex-shrink-0 ${item.is_milestone ? 'rotate-45' : ''}`}
              style={{ backgroundColor: statusColor }}
            />
            
            {/* Item title */}
            <span className="text-sm text-gray-700 truncate flex-1">
              {item.title}
            </span>
            
            {/* Progress (if not milestone) */}
            {!item.is_milestone && (
              <span className="text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                {item.percent_complete}%
              </span>
            )}

            {/* Personal badge */}
            {item.is_personal && (
              <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">
                Personal
              </span>
            )}
          </div>
        );
      })}

      {/* Empty state */}
      {rows.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-gray-400">
          <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="text-sm">No items yet</p>
          {canEdit && (
            <p className="text-xs mt-1">Click on the timeline to add</p>
          )}
        </div>
      )}
    </div>
  );
};

export default GanttSidebar;
