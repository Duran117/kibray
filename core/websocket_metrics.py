"""
WebSocket Metrics Collector

Collects and tracks real-time metrics for WebSocket connections:
- Active connections
- Message throughput
- Latency statistics
- Error rates
- Connection lifecycle
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional

from django.core.cache import cache
from django.utils import timezone


class WebSocketMetrics:
    """
    Singleton class for collecting WebSocket metrics
    
    Tracks:
    - Connection count (total, per user, per channel)
    - Message rate (messages/second)
    - Message latency (p50, p95, p99)
    - Error rate
    - Connection duration
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize metric storage"""
        # Connection tracking
        self.active_connections = set()
        self.connections_by_user = defaultdict(set)
        self.connections_by_channel = defaultdict(set)
        
        # Message tracking
        self.message_timestamps = deque(maxlen=10000)  # Last 10k messages
        self.message_latencies = deque(maxlen=1000)    # Last 1k latencies
        
        # Error tracking
        self.error_count = 0
        self.errors_by_type = defaultdict(int)
        self.last_errors = deque(maxlen=100)
        
        # Connection lifecycle
        self.connection_durations = deque(maxlen=1000)
        self.connections_created = 0
        self.connections_closed = 0
        
        # Timestamps
        self.start_time = time.time()
        self.last_reset = timezone.now()
    
    # ============================================================================
    # CONNECTION TRACKING
    # ============================================================================
    
    def connection_opened(self, connection_id: str, user_id: int, channel_id: Optional[int] = None):
        """Record new connection"""
        self.active_connections.add(connection_id)
        self.connections_by_user[user_id].add(connection_id)
        
        if channel_id:
            self.connections_by_channel[channel_id].add(connection_id)
        
        self.connections_created += 1
        
        # Store connection metadata
        cache.set(
            f'ws_conn:{connection_id}',
            {
                'user_id': user_id,
                'channel_id': channel_id,
                'opened_at': time.time(),
            },
            timeout=86400  # 24 hours
        )
    
    def connection_closed(self, connection_id: str):
        """Record connection closure"""
        # Get connection metadata
        conn_data = cache.get(f'ws_conn:{connection_id}')
        
        if conn_data:
            # Calculate duration
            duration = time.time() - conn_data['opened_at']
            self.connection_durations.append(duration)
            
            # Remove from tracking
            user_id = conn_data['user_id']
            channel_id = conn_data.get('channel_id')
            
            self.connections_by_user[user_id].discard(connection_id)
            if channel_id:
                self.connections_by_channel[channel_id].discard(connection_id)
        
        self.active_connections.discard(connection_id)
        self.connections_closed += 1
        
        # Clean up cache
        cache.delete(f'ws_conn:{connection_id}')
    
    def get_connection_count(self) -> Dict:
        """Get current connection counts"""
        return {
            'total': len(self.active_connections),
            'by_user': {
                user_id: len(conn_ids) 
                for user_id, conn_ids in self.connections_by_user.items() 
                if conn_ids
            },
            'by_channel': {
                channel_id: len(conn_ids)
                for channel_id, conn_ids in self.connections_by_channel.items()
                if conn_ids
            },
            'created': self.connections_created,
            'closed': self.connections_closed,
        }
    
    # ============================================================================
    # MESSAGE TRACKING
    # ============================================================================
    
    def message_sent(self, message_type: str, latency_ms: Optional[float] = None):
        """Record message sent"""
        self.message_timestamps.append(time.time())
        
        if latency_ms is not None:
            self.message_latencies.append(latency_ms)
    
    def get_message_rate(self, window_seconds: int = 60) -> float:
        """
        Get messages per second over time window
        
        Args:
            window_seconds: Time window in seconds (default 60)
            
        Returns:
            Messages per second
        """
        if not self.message_timestamps:
            return 0.0
        
        cutoff_time = time.time() - window_seconds
        recent_messages = [
            ts for ts in self.message_timestamps
            if ts > cutoff_time
        ]
        
        if not recent_messages:
            return 0.0
        
        return len(recent_messages) / window_seconds
    
    def get_latency_stats(self) -> Dict:
        """Get latency statistics"""
        if not self.message_latencies:
            return {
                'p50': 0,
                'p95': 0,
                'p99': 0,
                'avg': 0,
                'min': 0,
                'max': 0,
                'count': 0,
            }
        
        sorted_latencies = sorted(self.message_latencies)
        count = len(sorted_latencies)
        
        return {
            'p50': sorted_latencies[int(count * 0.5)] if count > 0 else 0,
            'p95': sorted_latencies[int(count * 0.95)] if count > 0 else 0,
            'p99': sorted_latencies[int(count * 0.99)] if count > 0 else 0,
            'avg': sum(sorted_latencies) / count if count > 0 else 0,
            'min': sorted_latencies[0] if count > 0 else 0,
            'max': sorted_latencies[-1] if count > 0 else 0,
            'count': count,
        }
    
    # ============================================================================
    # ERROR TRACKING
    # ============================================================================
    
    def error_occurred(self, error_type: str, error_message: str):
        """Record error"""
        self.error_count += 1
        self.errors_by_type[error_type] += 1
        self.last_errors.append({
            'type': error_type,
            'message': error_message,
            'timestamp': timezone.now().isoformat(),
        })
    
    def get_error_stats(self) -> Dict:
        """Get error statistics"""
        return {
            'total': self.error_count,
            'by_type': dict(self.errors_by_type),
            'recent': list(self.last_errors),
            'rate': self._calculate_error_rate(),
        }
    
    def _calculate_error_rate(self) -> float:
        """Calculate errors per minute"""
        if not self.last_errors:
            return 0.0
        
        # Count errors in last minute
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        recent_errors = [
            err for err in self.last_errors
            if datetime.fromisoformat(err['timestamp']) > one_minute_ago
        ]
        
        return len(recent_errors)
    
    # ============================================================================
    # CONNECTION LIFECYCLE
    # ============================================================================
    
    def get_connection_duration_stats(self) -> Dict:
        """Get connection duration statistics"""
        if not self.connection_durations:
            return {
                'avg': 0,
                'min': 0,
                'max': 0,
                'median': 0,
                'count': 0,
            }
        
        sorted_durations = sorted(self.connection_durations)
        count = len(sorted_durations)
        
        return {
            'avg': sum(sorted_durations) / count if count > 0 else 0,
            'min': sorted_durations[0] if count > 0 else 0,
            'max': sorted_durations[-1] if count > 0 else 0,
            'median': sorted_durations[count // 2] if count > 0 else 0,
            'count': count,
        }
    
    # ============================================================================
    # SUMMARY & REPORTING
    # ============================================================================
    
    def get_summary(self) -> Dict:
        """Get comprehensive metrics summary"""
        uptime = time.time() - self.start_time
        
        return {
            'timestamp': timezone.now().isoformat(),
            'uptime_seconds': uptime,
            'connections': self.get_connection_count(),
            'messages': {
                'rate_1m': self.get_message_rate(60),
                'rate_5m': self.get_message_rate(300),
                'rate_15m': self.get_message_rate(900),
                'latency': self.get_latency_stats(),
            },
            'errors': self.get_error_stats(),
            'connection_duration': self.get_connection_duration_stats(),
        }
    
    def reset(self):
        """Reset all metrics"""
        self._initialize()
    
    def export_to_cache(self):
        """Export metrics to cache for persistence"""
        summary = self.get_summary()
        cache.set('ws_metrics_summary', summary, timeout=3600)
        return summary


# Singleton instance
metrics = WebSocketMetrics()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_connection_opened(connection_id: str, user_id: int, channel_id: Optional[int] = None):
    """Helper to track connection opened"""
    metrics.connection_opened(connection_id, user_id, channel_id)


def track_connection_closed(connection_id: str):
    """Helper to track connection closed"""
    metrics.connection_closed(connection_id)


def track_message_sent(message_type: str, latency_ms: Optional[float] = None):
    """Helper to track message sent"""
    metrics.message_sent(message_type, latency_ms)


def track_error(error_type: str, error_message: str):
    """Helper to track error"""
    metrics.error_occurred(error_type, error_message)


def get_metrics_summary() -> Dict:
    """Helper to get metrics summary"""
    return metrics.get_summary()


def reset_metrics():
    """Helper to reset metrics"""
    metrics.reset()
