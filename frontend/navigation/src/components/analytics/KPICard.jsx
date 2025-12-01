import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import './KPICard.css';

const KPICard = ({ title, value, icon, trend, color = 'blue' }) => {
  const colorClass = `kpi-${color}`;
  const trendIcon = trend?.direction === 'up' ? <TrendingUp size={14} /> : <TrendingDown size={14} />;
  const trendClass = trend?.direction === 'up' ? 'trend-up' : 'trend-down';

  return (
    <div className={`kpi-card ${colorClass}`}>
      <div className="kpi-icon-wrapper">
        {icon}
      </div>
      <div className="kpi-content">
        <p className="kpi-title">{title}</p>
        <h3 className="kpi-value">{value}</h3>
        {trend && (
          <div className={`kpi-trend ${trendClass}`}>
            {trendIcon}
            <span>{trend.value}% vs last period</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default KPICard;
