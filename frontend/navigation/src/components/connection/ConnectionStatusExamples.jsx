import React, { useState } from 'react';
import ConnectionStatus from './ConnectionStatus';
import './ConnectionStatusExamples.css';

/**
 * ConnectionStatus Examples
 * 
 * Demonstrates all connection states and component modes
 */
const ConnectionStatusExamples = () => {
  const [currentStatus, setCurrentStatus] = useState('connected');

  const statuses = ['connected', 'connecting', 'reconnecting', 'disconnected'];

  return (
    <div className="connection-status-examples">
      <h2>Connection Status Indicator Examples</h2>

      {/* Example 1: All States */}
      <section className="example-section">
        <h3>1. All Connection States</h3>
        <div className="status-grid">
          {statuses.map((status) => (
            <div key={status} className="status-item">
              <ConnectionStatus status={status} />
            </div>
          ))}
        </div>
      </section>

      {/* Example 2: Interactive Status Switcher */}
      <section className="example-section">
        <h3>2. Interactive Status (Click to Change)</h3>
        <div className="status-interactive">
          <ConnectionStatus status={currentStatus} />
          <div className="button-group">
            {statuses.map((status) => (
              <button
                key={status}
                onClick={() => setCurrentStatus(status)}
                className={currentStatus === status ? 'active' : ''}
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Example 3: Without Text */}
      <section className="example-section">
        <h3>3. Icon + Dot Only (showText=false)</h3>
        <div className="status-grid">
          {statuses.map((status) => (
            <div key={status} className="status-item">
              <ConnectionStatus status={status} showText={false} />
            </div>
          ))}
        </div>
      </section>

      {/* Example 4: Compact Mode */}
      <section className="example-section">
        <h3>4. Compact Mode</h3>
        <div className="status-grid">
          {statuses.map((status) => (
            <div key={status} className="status-item">
              <ConnectionStatus status={status} compact />
            </div>
          ))}
        </div>
      </section>

      {/* Example 5: In Navigation Bar */}
      <section className="example-section">
        <h3>5. In Navigation Bar Context</h3>
        <div className="mock-navbar">
          <div className="navbar-left">
            <span className="navbar-logo">🏗️ Kibray</span>
          </div>
          <div className="navbar-right">
            <ConnectionStatus status="connected" compact />
          </div>
        </div>
        <div className="mock-navbar">
          <div className="navbar-left">
            <span className="navbar-logo">🏗️ Kibray</span>
          </div>
          <div className="navbar-right">
            <ConnectionStatus status="reconnecting" compact />
          </div>
        </div>
      </section>

      {/* Example 6: In Chat Panel Header */}
      <section className="example-section">
        <h3>6. In Chat Panel Header Context</h3>
        <div className="mock-chat-header">
          <span className="chat-title">Team Chat</span>
          <ConnectionStatus status="connected" />
        </div>
        <div className="mock-chat-header">
          <span className="chat-title">Team Chat</span>
          <ConnectionStatus status="disconnected" />
        </div>
      </section>

      {/* Example 7: Custom Styling */}
      <section className="example-section">
        <h3>7. With Custom Classes</h3>
        <div className="status-grid">
          <ConnectionStatus
            status="connected"
            className="custom-large"
          />
          <ConnectionStatus
            status="reconnecting"
            className="custom-bordered"
          />
        </div>
      </section>

      {/* Code Examples */}
      <section className="example-section code-examples">
        <h3>Usage Code Examples</h3>

        <div className="code-block">
          <h4>Basic Usage:</h4>
          <pre>{`import ConnectionStatus from './ConnectionStatus';
import { useWebSocket } from '../../hooks/useWebSocket';

function MyComponent() {
  const { connectionStatus } = useWebSocket();
  
  return <ConnectionStatus status={connectionStatus} />;
}`}</pre>
        </div>

        <div className="code-block">
          <h4>Compact Mode in Navbar:</h4>
          <pre>{`<div className="navbar-right">
  <ConnectionStatus 
    status={connectionStatus} 
    compact 
  />
</div>`}</pre>
        </div>

        <div className="code-block">
          <h4>Without Text:</h4>
          <pre>{`<ConnectionStatus 
  status={connectionStatus} 
  showText={false} 
/>`}</pre>
        </div>
      </section>
    </div>
  );
};

export default ConnectionStatusExamples;
