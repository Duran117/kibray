import React from 'react';
import { Wifi, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';
import './ConnectionStatus.css';

/**
 * ConnectionStatus Component
 * 
 * Displays WebSocket connection state with visual indicator
 * 
 * Props:
 * - status: 'connected' | 'connecting' | 'disconnected' | 'reconnecting'
 * - showText: boolean (default: true) - Show status text
 * - compact: boolean (default: false) - Compact mode (icon + dot only)
 * - className: string - Additional CSS classes
 * 
 * States:
 * - connected: Green dot, Wifi icon, "Connected" text
 * - connecting: Yellow dot, spinning RefreshCw icon, "Connecting..." text
 * - disconnected: Red dot, WifiOff icon, "Disconnected" text
 * - reconnecting: Orange dot, spinning RefreshCw icon, "Reconnecting..." text
 * 
 * Usage:
 * ```jsx
 * import { useWebSocket } from '../../hooks/useWebSocket';
 * 
 * function MyComponent() {
 *   const { connectionStatus } = useWebSocket();
 *   return <ConnectionStatus status={connectionStatus} />;
 * }
 * ```
 */
const ConnectionStatus = ({
  status = 'disconnected',
  showText = true,
  compact = false,
  className = '',
}) => {
  const getConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          text: 'Connected',
          color: 'green',
          dotClass: 'status-dot-green',
          spinning: false,
        };
      case 'connecting':
        return {
          icon: RefreshCw,
          text: 'Connecting...',
          color: 'yellow',
          dotClass: 'status-dot-yellow',
          spinning: true,
        };
      case 'reconnecting':
        return {
          icon: RefreshCw,
          text: 'Reconnecting...',
          color: 'orange',
          dotClass: 'status-dot-orange',
          spinning: true,
        };
      case 'disconnected':
      default:
        return {
          icon: WifiOff,
          text: 'Disconnected',
          color: 'red',
          dotClass: 'status-dot-red',
          spinning: false,
        };
    }
  };

  const config = getConfig();
  const Icon = config.icon;

  if (compact) {
    return (
      <div className={`connection-status connection-status-compact ${className}`} title={config.text}>
        <span className={`status-dot ${config.dotClass}`} />
        <Icon
          size={16}
          className={`status-icon ${config.spinning ? 'status-icon-spinning' : ''}`}
        />
      </div>
    );
  }

  return (
    <div className={`connection-status connection-status-${config.color} ${className}`}>
      <span className={`status-dot ${config.dotClass}`} />
      <Icon
        size={18}
        className={`status-icon ${config.spinning ? 'status-icon-spinning' : ''}`}
      />
      {showText && <span className="status-text">{config.text}</span>}
    </div>
  );
};

export default ConnectionStatus;
