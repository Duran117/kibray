import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigation } from '../../context/NavigationContext.jsx';
import WidgetGrid from './WidgetGrid.jsx';
import './DashboardPM.css';

const DashboardPM = () => {
  const { t } = useTranslation();
  const { currentContext } = useNavigation();
  return (
    <div className="dashboard-pm">
      <div className="dashboard-header">
        <h2>{t('dashboard.overview')}</h2>
        <p className="dashboard-sub">{t('dashboard.welcome_title')}</p>
      </div>
      <WidgetGrid projectId={currentContext.projectId} />
    </div>
  );
};

export default DashboardPM;
