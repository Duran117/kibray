# Phase 3 Quick Testing Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Start Server
```bash
cd /Users/jesus/Documents/kibray
python3 manage.py runserver
```

### Step 2: Open Dashboard
Navigate to: **http://localhost:8000/dashboard/pm/**
(Adjust URL based on your Django routing)

### Step 3: Visual Check ✓
- [ ] TasksWidget renders with filters (All/Active/Done)
- [ ] AlertsWidget shows alert count badge
- [ ] ChangeOrdersWidget displays CO numbers in monospace

### Step 4: Interaction Test ✓
- [ ] Click filter buttons → tasks update
- [ ] Drag a widget → position changes
- [ ] Refresh page → position persists

### Step 5: Console Check ✓
- Open DevTools (F12) → Console
- Expected: **0 errors**

---

## ✅ Success Criteria

If you see:
- ✅ All three widgets render without errors
- ✅ Filters work in TasksWidget
- ✅ Widgets can be dragged and repositioned
- ✅ Layout persists after refresh
- ✅ Zero JavaScript errors in console

**Then Phase 3 is VERIFIED and PRODUCTION READY! 🎉**

---

## 📋 Full Checklist

For comprehensive testing, see: **PHASE3_VERIFICATION_REPORT.md**

---

## 🐛 Troubleshooting

### Issue: "Page not found"
- Check Django URL routing
- Verify you're logged in (if auth required)
- Try: http://localhost:8000/ first

### Issue: "Static files not loading"
- Run: `python3 manage.py collectstatic --noinput`
- Check: `static/js/kibray-navigation.js` exists (156KB)
- Verify STATIC_URL in settings.py

### Issue: "Widgets not rendering"
- Open DevTools Console (F12)
- Look for JavaScript errors
- Check Network tab for failed requests

### Issue: "Can't drag widgets"
- Hover over widget (grip icon should appear)
- Ensure mouse is over grip icon
- Check console for React errors

---

## 📞 Need Help?

See detailed testing instructions in:
- **PHASE3_VERIFICATION_REPORT.md** (full manual testing checklist)
- **PHASE3_COMPLETE_REPORT.md** (feature documentation)

Bundle Info:
- Location: `/static/js/kibray-navigation.js`
- Size: 156 KB
- Build Time: 1,044ms
- Status: ✅ Ready
