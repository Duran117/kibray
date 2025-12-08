# PWA Testing Guide
# Steps 35-37: Testing and Validation

## Step 35: Build Production Bundle

```bash
cd frontend/navigation
npm run build
```

Expected output:
- `../../static/js/kibray-navigation.js` (minified)
- `../../static/js/service-worker.js` (Workbox injected)

## Step 36: Serve Production Build Locally

```bash
# Install serve if not already installed
npm install -g serve

# Serve the Django app (serves static files)
cd ../..
python manage.py runserver

# Or use serve directly on static files
cd static
serve -s . -p 8000
```

## Step 37: Run Lighthouse Audit

### Option 1: Chrome DevTools
1. Open Chrome/Edge browser
2. Navigate to `http://localhost:8000`
3. Open DevTools (F12)
4. Go to "Lighthouse" tab
5. Select:
   - ✅ Performance
   - ✅ Progressive Web App
   - ✅ Accessibility
   - ✅ Best Practices
   - ✅ SEO
6. Select "Mobile" device
7. Click "Analyze page load"

### Option 2: Lighthouse CLI

```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run audit
lighthouse http://localhost:8000 \
  --output html \
  --output-path ./lighthouse-report.html \
  --chrome-flags="--headless" \
  --only-categories=pwa,performance,accessibility

# Open report
open lighthouse-report.html
```

## PWA Criteria Checklist

Target: **95+ PWA Score**

### ✅ Required
- [ ] **Installable**: manifest.json with required properties
- [ ] **Service Worker**: Registered and active
- [ ] **HTTPS**: Must be served over HTTPS (or localhost)
- [ ] **Responsive**: Works on mobile and desktop
- [ ] **Fast Load**: < 3s on 3G
- [ ] **Offline**: Service worker caches resources
- [ ] **Add to Home Screen**: Prompt works

### ✅ Manifest Properties
- [ ] `name` (required)
- [ ] `short_name` (required)
- [ ] `start_url` (required)
- [ ] `display: standalone` (required)
- [ ] `icons` with 192x192 and 512x512 (required)
- [ ] `theme_color` (recommended)
- [ ] `background_color` (recommended)
- [ ] `description` (recommended)

### ✅ Service Worker
- [ ] Responds with 200 when offline
- [ ] Caches start_url
- [ ] Caches CSS and JS
- [ ] Has offline fallback page

### ✅ Performance
- [ ] First Contentful Paint < 2s
- [ ] Largest Contentful Paint < 2.5s
- [ ] Total Blocking Time < 300ms
- [ ] Cumulative Layout Shift < 0.1
- [ ] Speed Index < 3.4s

### ✅ Accessibility
- [ ] All images have alt text
- [ ] Proper heading hierarchy (h1 > h2 > h3)
- [ ] Sufficient color contrast (4.5:1 for text)
- [ ] Touch targets >= 44x44px
- [ ] Keyboard navigable
- [ ] ARIA labels where needed

## iOS Testing Checklist

### Safari on iPhone
1. Open Safari and navigate to app
2. Test basic navigation
3. Tap "Share" button in toolbar
4. Tap "Add to Home Screen"
5. Verify:
   - [ ] App icon appears on home screen
   - [ ] Splash screen shows on launch
   - [ ] App runs in standalone mode (no Safari UI)
   - [ ] Offline mode works
   - [ ] App remembers auth state

### Known iOS Limitations
- ⚠️ Push notifications require iOS 16.4+ and Add to Home Screen
- ⚠️ Service Worker has storage limits (~50MB)
- ⚠️ Background sync not supported
- ⚠️ Web Share API requires user gesture

## Android Testing Checklist

### Chrome on Android
1. Open Chrome and navigate to app
2. Wait for install banner to appear
3. Tap "Install" or "Add to Home Screen"
4. Verify:
   - [ ] App installs from banner
   - [ ] Icon appears in app drawer
   - [ ] Splash screen shows
   - [ ] Runs in standalone mode
   - [ ] Offline mode works
   - [ ] Push notifications work
   - [ ] App can be uninstalled

### Chrome DevTools Remote Debugging
```bash
# Enable USB debugging on Android device
# Connect via USB
# Open chrome://inspect in desktop Chrome
# Click "Inspect" on your device
```

## Common Issues & Fixes

### Issue: Service Worker not registering
**Fix**: Check browser console for errors. Ensure served over HTTPS or localhost.

### Issue: Manifest not detected
**Fix**: Verify Content-Type is `application/manifest+json`. Check manifest.json syntax.

### Issue: Icons not showing
**Fix**: Ensure icons exist at specified paths. Use absolute URLs or root-relative paths.

### Issue: Offline page not showing
**Fix**: Check service worker caches. Verify offline.html is precached.

### Issue: Install banner not appearing
**Fix**: Ensure all PWA criteria met. May need to wait 30s+ on first visit.

### Issue: Low Lighthouse score
**Fix**: 
- Compress images
- Minify JS/CSS
- Enable gzip compression
- Reduce JavaScript bundle size
- Eliminate render-blocking resources

## Testing Commands Summary

```bash
# Build production
cd frontend/navigation
npm run build

# Run Django server
cd ../..
python manage.py runserver

# Run Lighthouse audit
lighthouse http://localhost:8000 \
  --output html \
  --output-path ./PWA_LIGHTHOUSE_REPORT.html \
  --chrome-flags="--headless"

# Check service worker status
# Open DevTools > Application > Service Workers

# Check manifest
# Open DevTools > Application > Manifest

# Check offline mode
# Open DevTools > Network > Throttling > Offline
```

## Expected Results

### Lighthouse Scores (Target)
- **PWA**: 95+ / 100
- **Performance**: 85+ / 100
- **Accessibility**: 90+ / 100
- **Best Practices**: 95+ / 100
- **SEO**: 90+ / 100

### iOS Safari
- App installs successfully
- Runs standalone without browser UI
- Offline mode functional
- No console errors

### Android Chrome
- Install banner appears
- Push notifications work
- Offline queue processes on reconnect
- Smooth 60fps animations

## Next Steps After Testing

1. Fix any Lighthouse warnings
2. Optimize images and assets
3. Test on real devices (not just emulators)
4. Document any device-specific issues
5. Create PHASE_7_PWA_COMPLETE.md with results
6. Proceed to Production Deployment (Steps 39-62)
