# WebSocket Metrics Dashboard

**Phase 6 - Improvement #17: Real-time WebSocket Metrics Monitoring**

## 🎯 Overview

Complete implementation of a real-time metrics dashboard for monitoring WebSocket connections, message throughput, latency statistics, and error rates.

## ✨ Features Implemented

### Backend Metrics Collection
- ✅ **WebSocketMetrics Class**: Singleton metrics collector
- ✅ **Connection Tracking**: Active connections per user/channel
- ✅ **Message Rate**: Messages/second over time windows
- ✅ **Latency Statistics**: p50, p95, p99 percentiles
- ✅ **Error Tracking**: Error count, types, recent errors
- ✅ **Connection Duration**: Lifecycle statistics
- ✅ **Auto-Cleanup**: Removes stale data automatically

### REST API
- ✅ **Current Metrics**: GET /api/websocket/metrics/
- ✅ **Historical Data**: GET /api/websocket/metrics/history/
- ✅ **Staff-Only Access**: Security restriction
- ✅ **JSON Response**: Structured data format

### Frontend Dashboard
- ✅ **Live Dashboard**: Real-time metrics display
- ✅ **Auto-Refresh**: Updates every 5 seconds
- ✅ **Key Metrics Cards**: Connections, Message Rate, Latency, Errors
- ✅ **Detailed Stats**: Latency breakdown, connection duration
- ✅ **Error Display**: Recent errors with timestamps
- ✅ **Historical Chart**: Connection history visualization
- ✅ **Responsive Design**: Works on all screen sizes
- ✅ **Dark Mode**: Automatic dark mode support

### Celery Tasks
- ✅ **Periodic Collection**: Stores metrics every 5 minutes
- ✅ **Historical Storage**: Keeps 24 hours of history
- ✅ **Auto-Cleanup**: Removes old metrics (7+ days)

## 📁 Files Created

### Backend Files (440 lines)
1. **`core/websocket_metrics.py`** (350 lines)
   - WebSocketMetrics singleton class
   - Connection tracking methods
   - Message rate calculation
   - Latency statistics (percentiles)
   - Error tracking
   - Helper functions

2. **`core/api/views.py`** (70 lines added)
   - WebSocketMetricsView
   - WebSocketMetricsHistoryView

3. **`core/tasks.py`** (90 lines added)
   - collect_websocket_metrics task
   - cleanup_old_websocket_metrics task

### Frontend Files (828 lines)
1. **`frontend/navigation/src/components/metrics/WebSocketMetricsDashboard.jsx`** (468 lines)
   - Dashboard component
   - Auto-refresh functionality
   - Metrics visualization
   - Charts and graphs

2. **`frontend/navigation/src/components/metrics/WebSocketMetricsDashboard.css`** (360 lines)
   - Modern UI styling
   - Gradient effects
   - Responsive layout
   - Dark mode support

## 🚀 Quick Start

### View Dashboard

Add to your admin panel or navigation:
```jsx
import WebSocketMetricsDashboard from './components/metrics/WebSocketMetricsDashboard';

// In your admin routes
<Route path="/admin/metrics" element={<WebSocketMetricsDashboard />} />
```

### Track Metrics in Your Consumer

```python
from core.websocket_metrics import (
    track_connection_opened,
    track_connection_closed,
    track_message_sent,
    track_error
)

class MyChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        # Track connection
        track_connection_opened(
            connection_id=self.channel_name,
            user_id=self.scope['user'].id,
            channel_id=self.room_id
        )
    
    async def disconnect(self, close_code):
        # Track disconnection
        track_connection_closed(self.channel_name)
    
    async def receive(self, text_data):
        start_time = time.time()
        
        # Process message...
        
        # Track message with latency
        latency_ms = (time.time() - start_time) * 1000
        track_message_sent('chat_message', latency_ms)
    
    async def handle_error(self, error):
        # Track error
        track_error('websocket_error', str(error))
```

## 📊 Metrics Collected

### Connection Metrics
```json
{
  "total": 150,
  "by_user": {
    "1": 2,
    "2": 1,
    "3": 3
  },
  "by_channel": {
    "project_1": 50,
    "project_2": 100
  },
  "created": 1000,
  "closed": 850
}
```

### Message Metrics
```json
{
  "rate_1m": 25.5,
  "rate_5m": 23.2,
  "rate_15m": 22.8,
  "latency": {
    "p50": 15.5,
    "p95": 45.2,
    "p99": 78.3,
    "avg": 22.1,
    "min": 5.2,
    "max": 120.5,
    "count": 1000
  }
}
```

### Error Metrics
```json
{
  "total": 25,
  "by_type": {
    "websocket_error": 15,
    "authentication_error": 5,
    "rate_limit_error": 5
  },
  "rate": 2.5,
  "recent": [
    {
      "type": "websocket_error",
      "message": "Connection timeout",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ]
}
```

## 🔧 API Reference

### Get Current Metrics

**Endpoint:** `GET /api/websocket/metrics/`

**Authentication:** Required (Staff only)

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime_seconds": 86400,
  "connections": { ... },
  "messages": { ... },
  "errors": { ... },
  "connection_duration": { ... }
}
```

### Get Historical Metrics

**Endpoint:** `GET /api/websocket/metrics/history/?hours=24`

**Authentication:** Required (Staff only)

**Parameters:**
- `hours`: Number of hours (max 168 = 7 days)

**Response:**
```json
{
  "hours": 24,
  "interval_minutes": 5,
  "data_points": 288,
  "data": [ ... ]
}
```

## 📈 Dashboard Features

### Key Metrics Cards

1. **Active Connections** (Primary)
   - Total active connections
   - Connections created
   - Connections closed

2. **Message Rate** (Success)
   - Messages per second
   - 1-minute rate
   - 5-minute rate
   - 15-minute rate

3. **Latency** (Info)
   - p50 (median) latency
   - p95 latency
   - p99 latency

4. **Errors** (Danger)
   - Errors per minute
   - Total error count

### Detailed Statistics

- **Latency Stats**: avg, min, max, sample count
- **Connection Duration**: avg, median, min, max
- **Errors by Type**: Breakdown of error categories
- **Top Users**: Users with most connections

### Historical Chart

- Last 60 data points (5 minutes)
- Bar chart visualization
- Hover for exact values
- Auto-updates every 5 seconds

### Auto-Refresh

- Toggle on/off
- 5-second refresh interval
- Visual indicator when active
- Manual refresh button

## 🔄 Celery Setup

Add to your Celery beat schedule:

```python
# kibray_backend/celery.py

from celery.schedules import crontab

app.conf.beat_schedule = {
    # ... existing tasks ...
    
    # Collect WebSocket metrics every 5 minutes
    'collect-websocket-metrics': {
        'task': 'core.tasks.collect_websocket_metrics',
        'schedule': crontab(minute='*/5'),
    },
    
    # Clean up old metrics daily
    'cleanup-old-websocket-metrics': {
        'task': 'core.tasks.cleanup_old_websocket_metrics',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    },
}
```

## 🧪 Testing

### Test Metrics Collection

```python
from core.websocket_metrics import metrics

# Track some activity
metrics.connection_opened('conn_1', user_id=1, channel_id=123)
metrics.message_sent('chat', latency_ms=15.5)
metrics.message_sent('chat', latency_ms=20.3)
metrics.error_occurred('test_error', 'This is a test')

# Get summary
summary = metrics.get_summary()
print(summary)

# Clean up
metrics.reset()
```

### Test API Endpoint

```bash
# Get current metrics
curl http://localhost:8000/api/websocket/metrics/ \
  -H "Authorization: Bearer YOUR_STAFF_TOKEN"

# Get historical data
curl "http://localhost:8000/api/websocket/metrics/history/?hours=6" \
  -H "Authorization: Bearer YOUR_STAFF_TOKEN"
```

### Test Dashboard

1. Navigate to `/admin/metrics` (or your configured route)
2. Verify metrics are displayed
3. Check auto-refresh is working
4. Toggle auto-refresh off/on
5. Test manual refresh button
6. Check responsive design on mobile

## 🎨 Customization

### Change Refresh Interval

Edit `WebSocketMetricsDashboard.jsx`:
```jsx
// Change from 5 seconds to 10 seconds
refreshInterval.current = setInterval(fetchMetrics, 10000);
```

### Change Chart History Length

```jsx
// Keep last 120 data points (10 minutes at 5-second intervals)
return newHistory.slice(-120);
```

### Add Custom Metrics

In `websocket_metrics.py`:
```python
class WebSocketMetrics:
    def _initialize(self):
        # ... existing code ...
        self.custom_metric = 0
    
    def track_custom(self, value):
        self.custom_metric += value
    
    def get_summary(self):
        summary = super().get_summary()
        summary['custom'] = self.custom_metric
        return summary
```

## 📱 Responsive Design

- **Desktop**: 4-column grid for metrics
- **Tablet**: 2-column grid
- **Mobile**: Single column, stacked layout

## 🌙 Dark Mode

Automatically detects system preference:
- Dark background colors
- Adjusted text colors
- Maintained contrast ratios
- Gradient overlays preserved

## 🔐 Security

- **Staff-Only**: Only staff users can view metrics
- **No Sensitive Data**: No user PII in metrics
- **Rate Limiting**: Consider adding to API endpoints
- **Cache Timeout**: Metrics auto-expire after 24 hours

## 📊 Performance

### Metrics Storage
- In-memory data structures (fast)
- Redis cache for persistence
- Limited history (maxlen on deques)
- Auto-cleanup of old data

### Dashboard Performance
- Auto-refresh every 5 seconds
- Lightweight JSON payloads
- Client-side rendering
- No database queries during refresh

## 🚨 Troubleshooting

### "Only staff can view metrics"
- User must have `is_staff=True`
- Check user permissions
- Verify authentication token

### Metrics Not Updating
- Check Celery is running
- Verify beat schedule configured
- Check Redis connection
- Look for errors in logs

### Dashboard Not Refreshing
- Check browser console for errors
- Verify API endpoint is accessible
- Check authentication token
- Try manual refresh button

### High Memory Usage
- Adjust maxlen on deques
- Reduce history retention
- Increase cleanup frequency
- Monitor Redis memory

## 🎯 Use Cases

### Monitor System Health
- Track active connections
- Identify connection spikes
- Monitor error rates
- Detect anomalies

### Performance Optimization
- Identify slow operations (high latency)
- Find bottlenecks in message processing
- Optimize based on p95/p99 latency
- Track improvements over time

### Capacity Planning
- Monitor connection trends
- Plan infrastructure scaling
- Identify peak usage times
- Forecast resource needs

### Debugging
- View recent errors
- Track error patterns
- Correlate with system events
- Identify problematic users/channels

## 🔮 Future Enhancements

### Potential Additions
1. **Alerts**: Email/Slack when thresholds exceeded
2. **Advanced Charts**: Line graphs, heatmaps
3. **User Filtering**: Filter metrics by user/project
4. **Export**: Download metrics as CSV/JSON
5. **Comparison**: Compare time periods
6. **Predictions**: ML-based forecasting
7. **Integration**: Grafana/Prometheus support

## 📚 Resources

- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Django Channels](https://channels.readthedocs.io/)
- [Celery Beat](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [Redis Cache](https://redis.io/docs/)

## ✅ Completion Checklist

- [x] WebSocketMetrics class implemented
- [x] API endpoints created
- [x] Dashboard component built
- [x] Styling and responsive design
- [x] Celery tasks for data collection
- [x] Historical data storage
- [x] Auto-refresh functionality
- [x] Dark mode support
- [x] Error tracking
- [x] Documentation complete

---

**Phase 6 - Improvement #17: Metrics Dashboard - COMPLETE** ✅

This implementation provides:
- Real-time WebSocket monitoring
- Comprehensive metrics collection
- Beautiful dashboard interface
- Historical data tracking
- Auto-refresh capabilities
- Staff-only security
- Production-ready performance

The dashboard is ready for production use and provides valuable insights into WebSocket system health and performance.
