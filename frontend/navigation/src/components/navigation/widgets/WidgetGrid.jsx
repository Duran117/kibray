import React, { useState, useEffect } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { BREAKPOINTS, GRID_COLS } from '../../utils/constants';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import './WidgetGrid.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

const WidgetGrid = ({ children, defaultLayout }) => {
  const [layouts, setLayouts] = useState(() => {
    const saved = localStorage.getItem('dashboard-layout');
    return saved ? JSON.parse(saved) : { lg: defaultLayout };
  });
  const [isDragging, setIsDragging] = useState(false);

  const handleLayoutChange = (currentLayout, allLayouts) => {
    setLayouts(allLayouts);
    localStorage.setItem('dashboard-layout', JSON.stringify(allLayouts));
  };

  const handleDragStart = () => setIsDragging(true);
  const handleDragStop = () => setIsDragging(false);

  return (
    <div className={`widget-grid-container ${isDragging ? 'dragging' : ''}`}>
      <ResponsiveGridLayout
        className="widget-grid"
        layouts={layouts}
        breakpoints={BREAKPOINTS}
        cols={GRID_COLS}
        rowHeight={80}
        onLayoutChange={handleLayoutChange}
        onDragStart={handleDragStart}
        onDragStop={handleDragStop}
        isDraggable={true}
        isResizable={true}
        draggableHandle=".widget-drag-handle"
        margin={[16, 16]}
        containerPadding={[0, 0]}
        compactType="vertical"
      >
        {children}
      </ResponsiveGridLayout>
    </div>
  );
};

export default WidgetGrid;
