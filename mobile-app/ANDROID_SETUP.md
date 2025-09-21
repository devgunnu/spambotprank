# Android Development Setup Guide

## Quick Setup for Testing

Since you don't have Android SDK installed, here are your options for testing the call routing system:

### Option 1: Use Expo Go (Recommended for Quick Testing)

1. **Install Expo Go on your Android device:**
   - Download from Google Play Store: https://play.google.com/store/apps/details?id=host.exp.exponent

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Connect your device:**
   - Make sure your phone and computer are on the same WiFi network
   - Scan the QR code with Expo Go app
   - The app will load directly on your device

### Option 2: Install Android SDK (For Full Development)

1. **Install Android Studio:**
   ```bash
   # Download from: https://developer.android.com/studio
   # Or install via snap on Ubuntu:
   sudo snap install android-studio --classic
   ```

2. **Set up environment variables:**
   ```bash
   # Add to ~/.bashrc or ~/.profile
   export ANDROID_HOME=$HOME/Android/Sdk
   export PATH=$PATH:$ANDROID_HOME/emulator
   export PATH=$PATH:$ANDROID_HOME/platform-tools
   export PATH=$PATH:$ANDROID_HOME/tools
   export PATH=$PATH:$ANDROID_HOME/tools/bin
   ```

3. **Install platform tools:**
   - Open Android Studio
   - Go to Tools → SDK Manager
   - Install Android SDK Platform-Tools
   - Install at least one Android platform (API 31+ recommended)

4. **Create AVD (Android Virtual Device):**
   - In Android Studio: Tools → AVD Manager
   - Create Virtual Device
   - Choose a device definition
   - Select system image (API 31+)
   - Finish setup

### Option 3: Web Testing (Limited Functionality)

For UI and basic functionality testing:

```bash
npm run web
```

**Note:** Call detection won't work on web, but you can test the UI and backend communication.

## Testing Your Backend Server

Before testing the mobile app, ensure your Python FastAPI backend is running:

1. **Start your backend server** (replace with your actual server command):
   ```bash
   # Example - adjust for your setup
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Test backend endpoints manually:**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Test call routing
   curl -X POST http://localhost:8000/route-call \
     -H "Content-Type: application/json" \
     -d '{
       "callerId": "+1234567890",
       "timestamp": "2025-09-20T17:33:00Z",
       "deviceId": "test-device",
       "action": "route"
     }'
   ```

## Testing the Mobile App

### 1. Using Expo Go (Physical Device)

1. Start the development server:
   ```bash
   npm start
   ```

2. Scan QR code with Expo Go app on your Android device

3. Test the call routing system:
   - Open the app
   - Configure your backend URL (use your computer's IP address, not localhost)
   - Example: `http://192.168.1.100:8000` (replace with your actual IP)
   - Test backend connection
   - Enable call routing
   - Make a test call to your device

### 2. Using Android Emulator (After SDK Setup)

1. Start Android emulator:
   ```bash
   npm run android
   ```

2. Test with simulated calls (limited functionality in emulator)

### 3. Web Testing (UI Only)

1. Start web server:
   ```bash
   npm run web
   ```

2. Open http://localhost:8081 in your browser

3. Test UI components and backend communication

## Finding Your Computer's IP Address

To connect from your phone to your development server:

```bash
# On Linux/Mac
hostname -I
# or
ip addr show | grep inet

# Use this IP in your mobile app configuration
# Example: http://192.168.1.100:8000
```

## Troubleshooting

### Common Issues:

1. **"Cannot connect to backend"**
   - Ensure backend server is running
   - Use your computer's IP address, not localhost
   - Check firewall settings
   - Ensure phone and computer are on same network

2. **"Permissions denied"**
   - Grant all requested permissions in Android settings
   - Some permissions may require manual enabling

3. **"Call detection not working"**
   - Ensure app has phone permissions
   - Test on physical device (not emulator)
   - Some Android versions have stricter call access

4. **"App crashes on startup"**
   - Check that all dependencies are installed
   - Ensure you're using a physical device for call detection features

## Next Steps

1. **Start with Expo Go** for quick testing
2. **Set up your Python backend** with the required endpoints
3. **Test basic functionality** before implementing advanced features
4. **Consider Android SDK setup** for full development capabilities

## Production Deployment

When ready for production:

1. **Build APK/AAB:**
   ```bash
   npx eas build --platform android
   ```

2. **Consider using EAS (Expo Application Services)** for easier deployment

3. **Test thoroughly** on various Android versions and devices