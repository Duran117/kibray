
import React from 'react';
import { TrendingUp, TrendingDown, GripVertical } from 'lucide-react';
import './MetricWidget.css';

const MetricWidget = ({ title, value, icon, color = 'blue', trend }) => {
  const colorClass = `metric-${color}`;
  const trendIcon = trend?.direction === 'up' ? <TrendingUp size={14} /> : <TrendingDown size={14} />;
  const trendClass = trend?.direction === 'up' ?  'trend-up' : 'trend-down';

  return (
    <div className={`metric-widget ${colorClass}`}>
      <div className="widget-drag-handle">
        <GripVertical size={16} />
      </div>
      <div className="metric-header">
        <div className="metric-icon-wrapper">
          {icon}
        </div>
        {trend && (
          <div className={`metric-trend ${trendClass}`}>
            {trendIcon}
            <span>{trend.value}%</span>
          </div>
        )}
      </div>
      <div className="metric-content">
        <h3 className="metric-value">{value}</h3>
        <p className="metric-title">{title}</p>
      </div>
    </div>
  );
};

export default MetricWidget;
