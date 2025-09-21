# Testing Guide for Call Routing System

## Overview

This guide will help you test your call routing system step by step, from basic UI testing to full call interception.

## Prerequisites

1. **Mobile app** is set up and running
2. **Python backend** is running (use the provided `backend_example.py`)
3. **Network connectivity** between mobile device and backend server

## Step-by-Step Testing

### 1. Backend Server Setup

First, set up and test your backend server:

```bash
# Install FastAPI and dependencies
pip install fastapi uvicorn

# Run the example backend
python backend_example.py
```

Verify the server is running by visiting: http://localhost:8000/docs

### 2. Test Backend Endpoints

Test the backend independently before connecting the mobile app:

```bash
# Health check
curl http://localhost:8000/health

# Test call routing with different scenarios
# Normal call (should be allowed)
curl -X POST http://localhost:8000/route-call \
  -H "Content-Type: application/json" \
  -d '{
    "callerId": "+1555123456",
    "timestamp": "2025-09-20T17:33:00Z",
    "deviceId": "test-device",
    "action": "route"
  }'

# Spam call (should be redirected)
curl -X POST http://localhost:8000/route-call \
  -H "Content-Type: application/json" \
  -d '{
    "callerId": "Unknown Telemarketer",
    "timestamp": "2025-09-20T17:33:00Z",
    "deviceId": "test-device",
    "action": "route"
  }'

# Blocked number (should be rejected)
curl -X POST http://localhost:8000/route-call \
  -H "Content-Type: application/json" \
  -d '{
    "callerId": "+1234567890",
    "timestamp": "2025-09-20T17:33:00Z",
    "deviceId": "test-device",
    "action": "route"
  }'
```

### 3. Mobile App Testing

#### A. Web Version (UI Testing Only)

```bash
# Start web development server
npm run web
```

1. Open http://localhost:8081
2. Test the UI components:
   - Configuration section
   - Backend connection test
   - Enable/disable toggles
   - Statistics display

#### B. Physical Device Testing (Recommended)

1. **Setup Expo Go:**
   - Install Expo Go from Play Store
   - Ensure phone and computer are on same WiFi

2. **Start development server:**
   ```bash
   npm start
   ```

3. **Find your computer's IP address:**
   ```bash
   # Linux/Mac
   hostname -I
   # or
   ip route get 1 | awk '{print $7}'
   ```

4. **Configure the mobile app:**
   - Scan QR code with Expo Go
   - Update backend URL to use your IP (e.g., `http://192.168.1.100:8000`)
   - Test backend connection
   - Grant all requested permissions

### 4. Call Detection Testing

#### Phase 1: Basic Functionality

1. **Enable call routing in the app**
2. **Check permissions** - ensure all phone permissions are granted
3. **Monitor logs** in the development console

#### Phase 2: Simulated Testing

Since making actual test calls can be difficult, test the system components:

1. **Test backend communication:**
   - Use the "Test Connection" button
   - Check that configuration saves properly
   - Monitor network requests in logs

2. **Test UI updates:**
   - Enable/disable call routing
   - Check statistics display
   - Verify status indicators

#### Phase 3: Real Call Testing

**⚠️ Important:** Test with calls you control (friends/family) or VoIP services.

1. **Start call routing** in the app
2. **Make a test call** to the device
3. **Monitor the backend logs** for incoming requests
4. **Check app statistics** for call detection

#### Phase 4: Different Call Scenarios

Test various caller ID patterns:

1. **Normal number:** `+1555123456`
2. **Blocked number:** `+1234567890` (configured in backend)
3. **Spam indicators:** `"Unknown"`, `"Telemarketer"`, `"Private"`
4. **International numbers:** `+44...`, `+33...`

### 5. Testing Results Verification

#### Expected Backend Logs

When working correctly, you should see:

```
📞 Incoming call from +1555123456 on device abc123
✅ Allowing call from +1555123456

📞 Incoming call from Unknown Telemarketer on device abc123
🔄 Redirecting potential spam call from Unknown Telemarketer

📞 Incoming call from +1234567890 on device abc123
🚫 Blocking call from +1234567890
```

#### Expected Mobile App Behavior

1. **Configuration:**
   - Backend connection test succeeds
   - Settings save properly
   - Permissions are granted

2. **Call Detection:**
   - Statistics update with new calls
   - Status indicators show "Running"
   - No crashes or errors

3. **Integration:**
   - Backend receives call routing requests
   - App receives and processes responses
   - Actions are logged and displayed

### 6. Troubleshooting Common Issues

#### Backend Connection Issues

```bash
# Check if backend is accessible from mobile device
# Replace IP with your computer's IP
curl http://192.168.1.100:8000/health
```

**Solutions:**
- Verify backend is running on all interfaces (`0.0.0.0:8000`)
- Check firewall settings
- Ensure both devices are on same network
- Use IP address, not `localhost`

#### Call Detection Not Working

**Possible causes:**
- Insufficient permissions
- App not in foreground
- Platform limitations (iOS restrictions)
- Emulator instead of physical device

**Solutions:**
- Grant all phone-related permissions manually in Android settings
- Keep app in foreground during testing
- Test on physical Android device
- Check Android version compatibility

#### Performance Issues

**Monitoring:**
- Check memory usage in app
- Monitor network requests
- Watch for excessive API calls
- Verify efficient background processing

### 7. Production Testing Checklist

Before deploying to production:

- [ ] Backend server is deployed and accessible
- [ ] API authentication is implemented
- [ ] HTTPS is enabled for backend
- [ ] All error cases are handled gracefully
- [ ] App works in background/foreground modes
- [ ] Battery optimization is considered
- [ ] Privacy policy addresses call monitoring
- [ ] Local laws and regulations are complied with
- [ ] Extensive testing on various Android versions
- [ ] User consent mechanisms are in place

## Testing Data

Use this sample data for testing:

```json
{
  "normalCalls": [
    "+1555123456",
    "+1555987654",
    "John Doe",
    "Mom"
  ],
  "spamCalls": [
    "Unknown",
    "Telemarketer",
    "Private Number",
    "Suspected Spam"
  ],
  "blockedNumbers": [
    "+1234567890",
    "+1800SPAMMER"
  ]
}
```

## Monitoring and Logs

Key metrics to monitor:

1. **Call Detection Rate:** How many calls are detected vs. missed
2. **Backend Response Time:** API response latency
3. **Action Success Rate:** How often actions are executed successfully
4. **False Positives:** Legitimate calls incorrectly blocked
5. **False Negatives:** Spam calls not caught

## Next Steps

After successful testing:

1. **Deploy backend** to a reliable server
2. **Build production APK** with EAS Build
3. **Implement analytics** for monitoring
4. **Add user feedback** mechanisms
5. **Consider additional features** like whitelist management