# Push Notifications Setup Guide - OneSignal

## Overview
OneSignal provides free push notifications for web apps. This guide covers setup for Kibray PWA.

## 1. Create OneSignal Account

1. Go to https://onesignal.com/
2. Sign up for free account
3. Click "New App/Website"
4. Name: "Kibray Construction Management"
5. Select "Web Push" platform

## 2. Configure Web Push

### Site Settings:
- **Site URL**: https://your-domain.com (or http://localhost:8000 for testing)
- **Default Icon URL**: https://your-domain.com/static/icons/icon-192x192.png
- **Auto Resubscribe**: Enabled
- **Permission Prompt**: Native Browser Prompt

### Configuration Values:
After setup, OneSignal will provide:
- **App ID**: (save this - e.g., "12345678-1234-1234-1234-123456789012")
- **Safari Web ID**: (optional for Safari)
- **REST API Key**: (for server-side sending)

## 3. Add to Django Settings

Add to `kibray_backend/settings.py`:

```python
# OneSignal Configuration
ONESIGNAL_APP_ID = os.environ.get('ONESIGNAL_APP_ID', 'your-app-id-here')
ONESIGNAL_REST_API_KEY = os.environ.get('ONESIGNAL_REST_API_KEY', 'your-rest-api-key-here')
ONESIGNAL_USER_AUTH_KEY = os.environ.get('ONESIGNAL_USER_AUTH_KEY', '')  # Optional
```

Add to `.env`:
```
ONESIGNAL_APP_ID=your-actual-app-id
ONESIGNAL_REST_API_KEY=your-actual-rest-api-key
```

## 4. Install Python SDK (Optional)

If using server-side API calls:
```bash
pip install onesignal-sdk
```

Or use direct HTTP requests (recommended for simplicity).

## 5. Files to Create/Update

### Required Files:
1. ✅ `core/static/OneSignalSDKWorker.js` - Service worker for push
2. ✅ `core/notifications_push.py` - Helper functions to send notifications
3. ✅ Update `base.html` - Add OneSignal initialization
4. ✅ Update service worker registration

## 6. Notification Triggers

### Automatic Triggers:
- **Invoice Approved** → Notify PM
- **Change Order Created** → Notify Admin
- **Change Order Approved** → Notify Requester
- **Material Request Created** → Notify Inventory Manager
- **Material Received** → Notify Requester
- **Touch-up Assigned** → Notify Employee
- **Touch-up Completed** → Notify PM
- **Task Assigned** → Notify Employee
- **Project Budget Alert** → Notify PM + Admin

### User Preferences:
Users can:
- Enable/disable notifications per category
- Set quiet hours
- Choose notification sound

## 7. Testing

### Local Testing:
1. Use ngrok to expose localhost: `ngrok http 8000`
2. Update OneSignal site URL to ngrok URL
3. Test subscription in browser DevTools
4. Send test notification from OneSignal dashboard

### Production Testing:
1. Deploy to production
2. Update OneSignal site URL
3. Test on real mobile devices (iOS Safari, Android Chrome)
4. Verify notifications appear when app is closed

## 8. Implementation Checklist

- [ ] Create OneSignal account
- [ ] Get App ID and REST API Key
- [ ] Add credentials to settings.py and .env
- [ ] Create OneSignalSDKWorker.js
- [ ] Create notifications_push.py helper
- [ ] Update base.html with initialization
- [ ] Add notification triggers to views
- [ ] Test subscription flow
- [ ] Test sending notifications
- [ ] Test on mobile devices
- [ ] Add user preferences UI
- [ ] Document for team

## 9. Privacy & Permissions

### GDPR Compliance:
- Ask for explicit consent before subscribing
- Provide easy unsubscribe option
- Don't send spam
- Respect quiet hours

### Prompt Strategy:
- Don't prompt immediately on page load
- Prompt after user takes meaningful action
- Explain value of notifications
- Accept "Not Now" gracefully

## 10. Monitoring

OneSignal Dashboard shows:
- Total subscribers
- Notification delivery rate
- Click-through rate
- Platform breakdown (iOS/Android/Desktop)
- Engagement metrics

## 11. Cost

**Free Tier:**
- Up to 10,000 subscribers
- Unlimited notifications
- Basic analytics
- Perfect for small-medium businesses

**Paid Plans:**
- Start at $9/month for 10k+ subscribers
- Advanced segmentation
- A/B testing
- Priority support

## Resources

- OneSignal Docs: https://documentation.onesignal.com/docs/web-push-quickstart
- Django Integration: https://documentation.onesignal.com/docs/web-push-sdk
- Testing Guide: https://documentation.onesignal.com/docs/web-push-troubleshooting
