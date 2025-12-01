import React from 'react';
import { useNavigation } from '../../context/NavigationContext.jsx';
import WidgetGrid from './WidgetGrid.jsx';
import './DashboardPM.css';

const DashboardPM = () => {
  const { currentContext } = useNavigation();
  return (
    <div className="dashboard-pm">
      <div className="dashboard-header">
        <h2>Project Management Dashboard</h2>
        <p className="dashboard-sub">Overview metrics and operational insights</p>
      </div>
      <WidgetGrid projectId={currentContext.projectId} />
    </div>
  );
};

export default DashboardPM;
