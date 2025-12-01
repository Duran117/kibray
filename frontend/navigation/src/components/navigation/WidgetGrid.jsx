import React, { useEffect, useState } from 'react';
import GridLayout from 'react-grid-layout';
import MetricWidget from './widgets/MetricWidget.jsx';
import AlertsWidget from './widgets/AlertsWidget.jsx';
import TasksWidget from './widgets/TasksWidget.jsx';
import ChangeOrdersWidget from './widgets/ChangeOrdersWidget.jsx';
import { fetchProjectMetrics, fetchAlerts, fetchTasks, fetchChangeOrders } from './api.js';
import './WidgetGrid.css';

const STORAGE_KEY = 'navigation_widget_layout_v1';

const defaultLayout = [
  { i: 'metrics', x: 0, y: 0, w: 3, h: 4 },
  { i: 'alerts', x: 3, y: 0, w: 3, h: 6 },
  { i: 'tasks', x: 0, y: 4, w: 3, h: 6 },
  { i: 'change_orders', x: 3, y: 6, w: 3, h: 6 }
];

const WidgetGrid = ({ projectId }) => {
  const [layout, setLayout] = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || defaultLayout; } catch { return defaultLayout; }
  });
  const [metrics, setMetrics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [changeOrders, setChangeOrders] = useState([]);

  // Fetch data
  useEffect(() => {
    fetchProjectMetrics(projectId).then(setMetrics);
    fetchAlerts().then(setAlerts);
    fetchTasks().then(setTasks);
    fetchChangeOrders().then(setChangeOrders);
  }, [projectId]);

  const onLayoutChange = (newLayout) => {
    setLayout(newLayout);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newLayout));
  };

  return (
    <div className="widget-grid">
      <GridLayout
        className="layout"
        layout={layout}
        cols={6}
        rowHeight={32}
        width={1200}
        onLayoutChange={onLayoutChange}
        draggableHandle=".widget-header"
      >
        <div key="metrics" className="grid-item"><MetricWidget title="Budget Used" value={metrics?.budgetUsed || '--'} trend={{ direction: 'up', delta: '+2%' }} /></div>
        <div key="alerts" className="grid-item"><AlertsWidget alerts={alerts} /></div>
        <div key="tasks" className="grid-item"><TasksWidget tasks={tasks} /></div>
        <div key="change_orders" className="grid-item"><ChangeOrdersWidget changeOrders={changeOrders} /></div>
      </GridLayout>
    </div>
  );
};

export default WidgetGrid;
