import React from 'react';
import './ChangeOrdersWidget.css';

const ChangeOrdersWidget = ({ changeOrders }) => {
  return (
    <div className="widget change-orders-widget">
      <div className="widget-header"><h4>Change Orders</h4></div>
      <ul className="co-list">
        {changeOrders.map(co => (
          <li key={co.id} className={`co-item status-${co.status}`}>\n            <span className="co-title">{co.title}</span>\n            <span className="co-value">${co.amount.toLocaleString()}</span>\n          </li>
        ))}
        {changeOrders.length === 0 && <li className="empty">No change orders</li>}
      </ul>
    </div>
  );
};

export default ChangeOrdersWidget;
