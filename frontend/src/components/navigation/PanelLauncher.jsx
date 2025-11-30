import React from 'react';
import { useNavigation } from '../../context/NavigationContext.jsx';
import './PanelLauncher.css';

const PanelLauncher = () => {
  const { openPanel } = useNavigation();

  const openInfoPanel = () => {
    openPanel({
      key: 'info',
      title: 'General Info',
      width: '600px',
      content: (
        <div className="panel-body">
          <p>This is a sample panel. You can stack more panels by clicking below.</p>
          <button className="panel-action" onClick={openNestedPanel}>Open Nested Panel</button>
        </div>
      )
    });
  };

  const openNestedPanel = () => {
    openPanel({
      key: 'nested',
      title: 'Nested Detail',
      width: '520px',
      content: (
        <div className="panel-body">
          <p>Second level panel. Add forms or advanced controls here.</p>
          <button className="panel-action" onClick={openDeepPanel}>Deep Panel</button>
        </div>
      )
    });
  };

  const openDeepPanel = () => {
    openPanel({
      key: 'deep',
      title: 'Deep Panel Level 3',
      width: '480px',
      content: (
        <div className="panel-body">
          <p>Third level panel. Demonstrates stacking z-index & backdrop.</p>
        </div>
      )
    });
  };

  return (
    <div className="panel-launcher">
      <button onClick={openInfoPanel} className="launcher-btn">Open Info Panel</button>
      <button onClick={openNestedPanel} className="launcher-btn">Open Nested Direct</button>
      <button onClick={openDeepPanel} className="launcher-btn">Open Deep Direct</button>
    </div>
  );
};

export default PanelLauncher;
