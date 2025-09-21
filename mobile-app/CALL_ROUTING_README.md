# Call Routing System - Setup and Usage

## Overview

This Expo app implements a call detection and routing system that intercepts incoming calls and routes them through a Python FastAPI backend server. The app can detect incoming calls, communicate with your backend server, and take actions based on the server's response.

## Features

- **Call Detection**: Detects incoming phone calls using native Android/iOS APIs
- **Backend Integration**: Communicates with your Python FastAPI server
- **Call Routing**: Routes calls based on backend server decisions
- **Real-time Statistics**: Shows call statistics and routing status
- **Configuration UI**: Easy-to-use interface for configuration

## Setup Instructions

### 1. Backend Server Configuration

Update the backend URL in the app to point to your Python FastAPI server:

1. Open the app and go to the main screen
2. In the "Configuration" section, update the "Backend URL" field
3. If your server requires authentication, add an API key
4. Tap "Test Connection" to verify connectivity
5. Tap "Save Config" to save settings

### 2. Required Backend Endpoints

Your Python FastAPI server should implement these endpoints:

```python
# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# Call routing endpoint
@app.post("/route-call")
async def route_call(request: dict):
    # Expected request format:
    # {
    #   "callerId": "string",
    #   "timestamp": "ISO string",
    #   "deviceId": "string",
    #   "action": "route"
    # }
    
    # Return format:
    # {
    #   "success": bool,
    #   "action": "allow" | "reject" | "redirect",
    #   "redirectNumber": "optional phone number",
    #   "message": "optional message"
    # }
    pass

# Call status notification endpoint
@app.post("/call-status")
async def call_status(request: dict):
    # Called when call status changes
    # {
    #   "callerId": "string",
    #   "status": "answered" | "rejected" | "missed",
    #   "timestamp": "ISO string"
    # }
    pass

# Device registration endpoint
@app.post("/register-device")
async def register_device(request: dict):
    # {
    #   "deviceId": "string",
    #   "phoneNumber": "optional",
    #   "platform": "mobile",
    #   "timestamp": "ISO string"
    # }
    pass

# Routing configuration endpoint
@app.get("/routing-config")
async def get_routing_config():
    # Return routing configuration
    pass
```

### 3. Permissions

The app requests the following permissions:

**Android:**
- READ_PHONE_STATE: To detect incoming calls
- CALL_PHONE: To manage call routing
- ANSWER_PHONE_CALLS: To handle call actions
- MANAGE_OWN_CALLS: For call management
- RECORD_AUDIO: For call audio handling
- MODIFY_AUDIO_SETTINGS: For audio routing
- INTERNET: For backend communication
- FOREGROUND_SERVICE: For background operation

**iOS:**
- Microphone access: For call handling
- Contacts access: For call routing features

### 4. Running the App

1. Start your Python FastAPI backend server
2. Update the backend URL in the app configuration
3. Enable "Call Routing" in the app
4. Tap "Start Call Routing" to begin monitoring calls

## How It Works

1. **Call Detection**: The app monitors for incoming calls using `react-native-call-detection`
2. **Backend Communication**: When a call is detected, the app sends call details to your backend
3. **Decision Processing**: Your backend server decides what action to take (allow, reject, redirect)
4. **Action Execution**: The app executes the backend's decision
5. **Status Reporting**: Call status updates are sent back to the backend

## Limitations

- **iOS Restrictions**: Due to iOS security restrictions, call interception capabilities are limited
- **Android Permissions**: Requires sensitive permissions that may need user approval
- **Call Control**: Complete call blocking/redirecting has platform limitations
- **Background Processing**: May require foreground service for continuous operation

## Troubleshooting

### App won't start call routing:
1. Check that all permissions are granted
2. Verify backend server is running and accessible
3. Test backend connection using the "Test Connection" button

### Calls not being detected:
1. Ensure READ_PHONE_STATE permission is granted
2. Check that the app has necessary call-related permissions
3. Verify the app is running in the foreground or as a background service

### Backend communication issues:
1. Check network connectivity
2. Verify backend URL is correct and accessible
3. Check API key if authentication is required
4. Review backend server logs for errors

## Development Notes

- The app uses TypeScript for type safety
- Services are organized in the `/services` directory
- UI components are in the `/components` directory
- Configuration is managed through the `CallRoutingService`

## Security Considerations

- Store API keys securely
- Use HTTPS for backend communication
- Implement proper authentication in your backend
- Be aware of privacy implications of call monitoring
- Comply with local laws regarding call interception

## Testing

To test the system:

1. Configure the app with your backend URL
2. Start call routing
3. Make a test call to the device
4. Monitor backend logs to see call routing requests
5. Check app statistics to verify call detection

Remember to test on a physical device as call detection won't work in simulators.