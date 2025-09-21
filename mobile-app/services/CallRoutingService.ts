import * as Device from 'expo-device';
import { Alert } from 'react-native';
import BackendApiService, { CallRouteRequest, CallRouteResponse } from './BackendApiService';
import CallDetectionService, { CallEvent } from './CallDetectionService';

export interface CallRoutingConfig {
  enabled: boolean;
  backendUrl: string;
  apiKey?: string;
  autoReject: boolean;
  forwardToBackend: boolean;
}

export interface CallRoutingStats {
  totalCalls: number;
  routedCalls: number;
  rejectedCalls: number;
  lastCall?: {
    callerId: string;
    timestamp: Date;
    action: string;
  };
}

class CallRoutingService {
  private config: CallRoutingConfig = {
    enabled: false,
    backendUrl: 'http://localhost:8000',
    autoReject: false,
    forwardToBackend: true
  };

  private stats: CallRoutingStats = {
    totalCalls: 0,
    routedCalls: 0,
    rejectedCalls: 0
  };

  private isInitialized: boolean = false;
  private deviceId: string = '';

  async initialize(config: Partial<CallRoutingConfig> = {}): Promise<boolean> {
    try {
      // Update configuration
      this.config = { ...this.config, ...config };
      
      // Get device ID
      this.deviceId = Device.osInternalBuildId || Device.modelId || 'unknown-device';
      
      // Configure backend service
      BackendApiService.updateConfig({
        baseUrl: this.config.backendUrl,
        apiKey: this.config.apiKey
      });

      // Test backend connection
      const isBackendConnected = await BackendApiService.testConnection();
      if (!isBackendConnected) {
        console.warn('Backend server is not reachable. Call routing may not work properly.');
      }

      // Register device with backend
      await BackendApiService.registerDevice(this.deviceId);

      this.isInitialized = true;
      console.log('Call routing service initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize call routing service:', error);
      return false;
    }
  }

  async startCallRouting(): Promise<boolean> {
    if (!this.isInitialized) {
      console.error('Call routing service not initialized. Call initialize() first.');
      return false;
    }

    if (!this.config.enabled) {
      console.warn('Call routing is disabled in configuration');
      return false;
    }

    const success = await CallDetectionService.startCallDetection({
      onIncomingCall: this.handleIncomingCall.bind(this),
      onCallAnswered: this.handleCallAnswered.bind(this),
      onCallDisconnected: this.handleCallDisconnected.bind(this)
    });

    if (success) {
      console.log('Call routing started successfully');
    } else {
      console.error('Failed to start call routing');
    }

    return success;
  }

  stopCallRouting(): void {
    CallDetectionService.stopCallDetection();
    console.log('Call routing stopped');
  }

  private async handleIncomingCall(event: CallEvent): Promise<void> {
    console.log('🔄 Processing incoming call:', event.callerId);
    
    this.stats.totalCalls++;
    this.stats.lastCall = {
      callerId: event.callerId,
      timestamp: event.timestamp,
      action: 'processing'
    };

    try {
      // Route call through backend
      const routeRequest: CallRouteRequest = {
        callerId: event.callerId,
        timestamp: event.timestamp.toISOString(),
        deviceId: this.deviceId,
        action: 'route'
      };

      const response: CallRouteResponse = await BackendApiService.routeCall(routeRequest);
      
      await this.executeCallAction(event, response);
      
    } catch (error) {
      console.error('Error processing incoming call:', error);
      // Default action if backend fails
      await this.executeCallAction(event, {
        success: false,
        action: 'allow',
        message: 'Processing failed, allowing call'
      });
    }
  }

  private async executeCallAction(event: CallEvent, response: CallRouteResponse): Promise<void> {
    console.log('📞 Executing call action:', response.action, 'for', event.callerId);

    switch (response.action) {
      case 'allow':
        // Let the call proceed normally
        console.log('✅ Allowing call from', event.callerId);
        this.updateStats('allowed');
        break;

      case 'reject':
        // Attempt to reject the call (limited capabilities in React Native)
        console.log('❌ Rejecting call from', event.callerId);
        this.rejectCall(event);
        this.stats.rejectedCalls++;
        this.updateStats('rejected');
        break;

      case 'redirect':
        // Redirect to backend server or another number
        console.log('🔄 Redirecting call from', event.callerId);
        this.redirectCall(event, response.redirectNumber);
        this.stats.routedCalls++;
        this.updateStats('redirected');
        break;

      default:
        console.log('⚠️ Unknown action:', response.action);
        this.updateStats('unknown');
    }

    // Notify backend about the action taken
    await BackendApiService.notifyCallStatus(event.callerId, 'answered');
  }

  private rejectCall(event: CallEvent): void {
    // Note: Direct call rejection is limited in React Native for security reasons
    // This is more of a notification/logging mechanism
    
    if (this.config.autoReject) {
      Alert.alert(
        'Call Blocked',
        `Blocked incoming call from ${event.callerId}`,
        [{ text: 'OK' }]
      );
    }
    
    console.log('Call rejection attempted for:', event.callerId);
  }

  private redirectCall(event: CallEvent, redirectNumber?: string): void {
    if (redirectNumber) {
      // Attempt to redirect to the specified number
      console.log(`Redirecting call to: ${redirectNumber}`);
      
      // This would typically involve more complex call control APIs
      // For now, we'll show a notification
      Alert.alert(
        'Call Redirected',
        `Call from ${event.callerId} is being redirected to ${redirectNumber}`,
        [{ text: 'OK' }]
      );
    } else {
      console.log('No redirect number provided');
    }
  }

  private async handleCallAnswered(event: CallEvent): Promise<void> {
    console.log('📞 Call answered:', event.callerId);
    await BackendApiService.notifyCallStatus(event.callerId, 'answered');
  }

  private async handleCallDisconnected(event: CallEvent): Promise<void> {
    console.log('📞 Call disconnected:', event.callerId);
    await BackendApiService.notifyCallStatus(event.callerId, 'missed');
  }

  private updateStats(action: string): void {
    if (this.stats.lastCall) {
      this.stats.lastCall.action = action;
    }
  }

  // Public methods for configuration and status

  updateConfiguration(config: Partial<CallRoutingConfig>): void {
    this.config = { ...this.config, ...config };
    
    if (config.backendUrl || config.apiKey) {
      BackendApiService.updateConfig({
        baseUrl: this.config.backendUrl,
        apiKey: this.config.apiKey
      });
    }
  }

  getConfiguration(): CallRoutingConfig {
    return { ...this.config };
  }

  getStats(): CallRoutingStats {
    return { ...this.stats };
  }

  isRunning(): boolean {
    return CallDetectionService.isRunning();
  }

  async testBackendConnection(): Promise<boolean> {
    return await BackendApiService.testConnection();
  }

  resetStats(): void {
    this.stats = {
      totalCalls: 0,
      routedCalls: 0,
      rejectedCalls: 0
    };
  }
}

export default new CallRoutingService();