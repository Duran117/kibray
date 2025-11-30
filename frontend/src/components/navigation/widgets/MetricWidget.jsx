import React from 'react';
import './MetricWidget.css';

const MetricWidget = ({ title, value, trend }) => {
  return (
    <div className="widget metric-widget">
      <div className="widget-header">
        <h4>{title}</h4>
      </div>
      <div className="metric-main">
        <span className="metric-value">{value}</span>
        {trend && <span className={`metric-trend ${trend.direction}`}>{trend.delta}</span>}
      </div>
    </div>
  );
};

export default MetricWidget;
