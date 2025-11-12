# 📱 iOS App Setup Guide - Kibray Mobile

## 🎯 Overview

This guide walks you through the **easiest path** to create an iOS app for Kibray using **Capacitor** - a tool that wraps your web interface (or a simple web view) into a native iOS app, allowing you to use Swift features and submit to the App Store.

**Why Capacitor?**
- ✅ Quickest path from Django backend to App Store
- ✅ Reuses existing web UI with minimal changes
- ✅ Access to native iOS features (camera, push notifications, biometrics)
- ✅ Much simpler than native Swift + SwiftUI from scratch

---

## 📋 Prerequisites

### Required Tools

1. **macOS** with Xcode installed (free from Mac App Store)
2. **Node.js** (version 18+): Download from [nodejs.org](https://nodejs.org/)
3. **CocoaPods**: Install via terminal:
   ```bash
   sudo gem install cocoapods
   ```
4. **Xcode Command Line Tools**:
   ```bash
   xcode-select --install
   ```

### Apple Developer Account

- **Free account**: Test on your own device (7-day certificate)
- **Paid account** ($99/year): Required for App Store submission

Sign up at [developer.apple.com](https://developer.apple.com/)

---

## 🚀 Step 1: Create Capacitor Project

### Option A: Web-Based App (Easiest)

Create a simple web wrapper that loads your Django site:

```bash
# Create project directory
mkdir kibray-ios
cd kibray-ios

# Initialize npm project
npm init -y

# Install Capacitor
npm install @capacitor/core @capacitor/cli @capacitor/ios

# Initialize Capacitor
npx cap init
```

**When prompted**:
- App name: `Kibray`
- Package ID: `com.yourcompany.kibray` (must be unique, lowercase)
- Web asset directory: `www` (we'll create this)

### Create Web Assets

Create a basic `www/` folder with your app entry point:

```bash
mkdir www
```

**File: `www/index.html`**:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kibray</title>
  <style>
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFace, sans-serif;
    }
    iframe {
      width: 100vw;
      height: 100vh;
      border: none;
    }
  </style>
</head>
<body>
  <!-- Embed your Django web app -->
  <iframe src="https://kibray-backend.onrender.com/login/" allowfullscreen></iframe>
  <script src="capacitor.js"></script>
</body>
</html>
```

**OR** use a native-looking login screen:

**File: `www/index.html`** (Native-style):
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kibray</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .login-card {
      background: white;
      border-radius: 20px;
      padding: 40px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      max-width: 400px;
      width: 100%;
    }
    h1 {
      font-size: 28px;
      margin-bottom: 30px;
      text-align: center;
      background: linear-gradient(135deg, #667eea, #764ba2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    input {
      width: 100%;
      padding: 15px;
      margin-bottom: 15px;
      border: 2px solid #e0e0e0;
      border-radius: 10px;
      font-size: 16px;
      transition: border 0.3s;
    }
    input:focus {
      outline: none;
      border-color: #667eea;
    }
    button {
      width: 100%;
      padding: 15px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
    }
    .error {
      color: #e53e3e;
      font-size: 14px;
      margin-bottom: 10px;
      display: none;
    }
  </style>
</head>
<body>
  <div class="login-card">
    <h1>Kibray</h1>
    <div class="error" id="error"></div>
    <form id="login-form">
      <input type="text" id="username" placeholder="Username" required>
      <input type="password" id="password" placeholder="Password" required>
      <button type="submit">Sign In</button>
    </form>
  </div>
  
  <script src="capacitor.js"></script>
  <script>
    const API_BASE = 'https://kibray-backend.onrender.com/api/v1';
    
    document.getElementById('login-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      const errorEl = document.getElementById('error');
      
      try {
        const response = await fetch(`${API_BASE}/auth/login/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
          const { access, refresh } = await response.json();
          localStorage.setItem('access_token', access);
          localStorage.setItem('refresh_token', refresh);
          
          // Redirect to dashboard (load Django web UI)
          window.location.href = 'https://kibray-backend.onrender.com/dashboard/';
        } else {
          errorEl.textContent = 'Invalid credentials';
          errorEl.style.display = 'block';
        }
      } catch (err) {
        errorEl.textContent = 'Connection error';
        errorEl.style.display = 'block';
      }
    });
  </script>
</body>
</html>
```

---

## 🍎 Step 2: Add iOS Platform

```bash
# Add iOS platform (creates ios/ folder with Xcode project)
npx cap add ios

# Sync web assets to iOS project
npx cap sync
```

This creates an `ios/App/` folder with a full Xcode project.

---

## 📱 Step 3: Install Native Plugins

### Camera Plugin (for damage reports, color samples)

```bash
npm install @capacitor/camera
npx cap sync
```

**Usage in JavaScript**:
```javascript
import { Camera, CameraResultType } from '@capacitor/camera';

async function takeDamagePhoto() {
  const photo = await Camera.getPhoto({
    resultType: CameraResultType.Uri,
    quality: 90
  });
  
  // Upload to Django API
  const formData = new FormData();
  formData.append('photo', {
    uri: photo.path,
    name: 'damage.jpg',
    type: 'image/jpeg'
  });
  formData.append('project', '1');
  formData.append('title', 'Water damage');
  
  await fetch('https://kibray-backend.onrender.com/api/v1/damage-reports/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
}
```

### Push Notifications Plugin

```bash
npm install @capacitor/push-notifications
npx cap sync
```

**Usage**:
```javascript
import { PushNotifications } from '@capacitor/push-notifications';

// Request permission
await PushNotifications.requestPermissions();

// Register for push
await PushNotifications.register();

// Listen for token (send to Django backend)
PushNotifications.addListener('registration', (token) => {
  console.log('Push token:', token.value);
  // Save to user profile via API
});

// Handle incoming notifications
PushNotifications.addListener('pushNotificationReceived', (notification) => {
  console.log('Notification:', notification);
});
```

### Other Useful Plugins

```bash
# Filesystem (for offline caching)
npm install @capacitor/filesystem

# Geolocation (for site check-ins)
npm install @capacitor/geolocation

# Haptics (for feedback)
npm install @capacitor/haptics
```

---

## 🛠 Step 4: Open in Xcode

```bash
npx cap open ios
```

This opens the project in Xcode.

### Xcode Configuration

1. **Select target**: Click `App` in the left sidebar
2. **General tab**:
   - **Display Name**: Kibray
   - **Bundle Identifier**: `com.yourcompany.kibray` (must match Capacitor config)
   - **Version**: 1.0.0
   - **Build**: 1
   - **Deployment Target**: iOS 13.0 or later

3. **Signing & Capabilities**:
   - **Team**: Select your Apple Developer account
   - **Automatically manage signing**: ✅ (checked)
   - If you see "Failed to create provisioning profile", ensure Bundle ID is unique

4. **Add Capabilities** (for plugins):
   - Click **+ Capability**
   - Add **Push Notifications** (for push plugin)
   - Add **Background Modes** → Check "Remote notifications"

5. **Privacy Permissions** (Info.plist):
   - Click `Info.plist` in left sidebar
   - Add these keys (right-click → Add Row):
     - `NSCameraUsageDescription`: "Kibray needs camera access to capture damage photos and color samples"
     - `NSPhotoLibraryUsageDescription`: "Kibray needs photo access to attach images to reports"
     - `NSLocationWhenInUseUsageDescription`: "Kibray uses location for site check-ins" (optional)

---

## ▶️ Step 5: Run on Simulator or Device

### Simulator (no Apple account needed)

1. Select a simulator device from top bar (e.g., "iPhone 15 Pro")
2. Click **Play** button (▶️) or press `Cmd+R`
3. App launches in simulator

### Real Device (requires Apple Developer account)

1. Connect iPhone via USB
2. **Trust computer** on iPhone when prompted
3. Select your iPhone from device dropdown in Xcode
4. Click **Play** (▶️)
5. If "Developer Mode" disabled on iPhone:
   - Go to iPhone Settings → Privacy & Security → Developer Mode → Enable
   - Restart iPhone
6. If "Untrusted Developer" error:
   - iPhone Settings → General → VPN & Device Management → Trust your developer profile

---

## 🔧 Step 6: Customize App (Optional)

### App Icon

1. Create 1024x1024 PNG icon
2. Use [App Icon Generator](https://www.appicon.co/) to generate all sizes
3. In Xcode, click `Assets.xcassets` → `AppIcon`
4. Drag generated icons into slots

### Splash Screen

1. Create 2732x2732 PNG (centered logo on solid background)
2. Click `Assets.xcassets` → `Splash`
3. Drag image into 3x slot

### Modify Capacitor Config

**File: `capacitor.config.json`**:
```json
{
  "appId": "com.yourcompany.kibray",
  "appName": "Kibray",
  "webDir": "www",
  "server": {
    "url": "https://kibray-backend.onrender.com",
    "cleartext": false,
    "androidScheme": "https"
  },
  "ios": {
    "contentInset": "always",
    "scrollEnabled": true
  },
  "plugins": {
    "SplashScreen": {
      "launchShowDuration": 2000,
      "backgroundColor": "#667eea"
    },
    "PushNotifications": {
      "presentationOptions": ["badge", "sound", "alert"]
    }
  }
}
```

After changes, run:
```bash
npx cap sync
```

---

## 📦 Step 7: Build for Release

### Archive for App Store

1. In Xcode, select **Any iOS Device (arm64)** from device dropdown
2. **Product** → **Archive** (wait 5-10 min for build)
3. Organizer window opens with your archive
4. Click **Distribute App**
5. Select **App Store Connect**
6. Follow wizard (sign with certificate, upload to Apple)

### App Store Connect Setup

1. Go to [App Store Connect](https://appstoreconnect.apple.com/)
2. **My Apps** → **+ (New App)**
3. Fill in:
   - **Name**: Kibray
   - **Language**: English
   - **Bundle ID**: Select your bundle ID
   - **SKU**: kibray-ios-app (any unique ID)
4. Upload screenshots (required):
   - 6.5" iPhone: 1242x2688 px (3 images minimum)
   - 5.5" iPhone: 1242x2208 px
5. Fill in app description, keywords, support URL
6. Submit for review (initial review takes 1-3 days)

---

## 🔐 Push Notifications Setup (APNs)

### Generate APNs Certificate

1. Go to [Apple Developer Portal](https://developer.apple.com/account/resources/certificates/list)
2. **Certificates** → **+**
3. Select **Apple Push Notification service SSL (Sandbox & Production)**
4. Select your App ID
5. Download `.p8` key file
6. Note **Key ID** and **Team ID**

### Configure Django Backend

Update `kibray_backend/settings.py`:

```python
# APNs Configuration
APNS_AUTH_KEY = os.environ.get('APNS_AUTH_KEY')  # Contents of .p8 file
APNS_AUTH_KEY_ID = os.environ.get('APNS_AUTH_KEY_ID')  # e.g., "ABC123XYZ"
APNS_TEAM_ID = os.environ.get('APNS_TEAM_ID')  # e.g., "XYZ123ABC"
APNS_TOPIC = 'com.yourcompany.kibray'  # Your bundle ID
APNS_USE_SANDBOX = DEBUG  # True for dev, False for prod
```

Install APNs library:
```bash
pip install py-apns
```

**Send push from Django**:
```python
from apns2.client import APNsClient
from apns2.payload import Payload

client = APNsClient(
    credentials='/path/to/key.p8',
    use_sandbox=settings.APNS_USE_SANDBOX
)

payload = Payload(
    alert="New task assigned",
    badge=5,
    sound="default"
)

client.send_notification(
    token_hex='device_token_from_ios_app',
    notification=payload,
    topic='com.yourcompany.kibray'
)
```

---

## 🎉 Next Steps After App Store Approval

1. **Monitor Crashes**: Use Xcode Organizer → Crashes
2. **Analytics**: Integrate Firebase Analytics or App Store Connect analytics
3. **Updates**: Increment version number, rebuild, resubmit
4. **TestFlight**: Use for beta testing before production release

---

## 🆘 Troubleshooting

### "Failed to register bundle identifier"
- Your bundle ID is taken. Change in `capacitor.config.json` and Xcode

### "No profiles for 'com.yourcompany.kibray' were found"
- Go to Apple Developer Portal → Certificates, Identifiers & Profiles → Identifiers
- Create App ID matching your bundle ID

### "Could not launch app on device"
- Enable Developer Mode on iPhone (Settings → Privacy & Security → Developer Mode)
- Trust developer certificate (Settings → General → VPN & Device Management)

### White screen in app
- Check `www/index.html` exists and is correct
- Run `npx cap sync` after changes
- Check browser console in Safari (Develop → Simulator → index.html)

### API calls failing (CORS errors)
- Verify backend CORS settings include `capacitor://localhost`
- Check API URL in `capacitor.config.json` is correct

---

## 📚 Additional Resources

- [Capacitor Docs](https://capacitorjs.com/docs)
- [Capacitor iOS Guide](https://capacitorjs.com/docs/ios)
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)

---

## ✅ Checklist Before App Store Submission

- [ ] App tested on real device
- [ ] All API endpoints working (login, notifications, chat, tasks, etc.)
- [ ] Camera permission working (damage reports, color samples)
- [ ] Push notifications configured (optional for v1)
- [ ] App icon and splash screen added
- [ ] Version and build number set in Xcode
- [ ] Screenshots captured (3+ per device size)
- [ ] App Store description written
- [ ] Privacy policy URL added (required)
- [ ] Support URL added
- [ ] Age rating set (likely 4+)
- [ ] Signed with production certificate (not development)

---

**¡Éxito con tu app!** 🚀

Once approved, your users can download Kibray from the App Store and start managing construction projects on the go.
