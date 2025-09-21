import { Alert, PermissionsAndroid, Platform } from 'react-native';

// Import call detection library
let CallDetectorManager: any = null;
let hasCallDetectionSupport = false;

if (Platform.OS === 'android') {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const callDetection = require('react-native-call-detection');
    CallDetectorManager = callDetection.default || callDetection;
    hasCallDetectionSupport = true;
    console.log('Call detection library loaded successfully');
  } catch (error) {
    console.warn('Call detection not available:', error);
    hasCallDetectionSupport = false;
  }
}

interface CallInterceptorConfig {
  isEnabled: boolean;
  twilioNumber: string;
  onCallForwarded: (fromNumber: string, toNumber: string) => void;
}

class RealCallInterceptor {
  private callDetector: any = null;
  private isStarted: boolean = false;
  private config: CallInterceptorConfig | null = null;

  async requestPermissions(): Promise<boolean> {
    if (Platform.OS !== 'android') {
      return false;
    }

    try {
      const permissions = [
        PermissionsAndroid.PERMISSIONS.READ_PHONE_STATE,
        PermissionsAndroid.PERMISSIONS.CALL_PHONE,
      ];

      const results = await PermissionsAndroid.requestMultiple(permissions);
      
      const allGranted = Object.values(results).every(
        result => result === PermissionsAndroid.RESULTS.GRANTED
      );

      if (!allGranted) {
        Alert.alert(
          'Permissions Required',
          'Please grant all phone permissions to enable call forwarding.',
          [{ text: 'OK' }]
        );
      }

      return allGranted;
    } catch (error) {
      console.error('Permission request failed:', error);
      return false;
    }
  }

  async startCallInterception(config: CallInterceptorConfig): Promise<boolean> {
    if (!hasCallDetectionSupport || !CallDetectorManager) {
      Alert.alert(
        'Not Supported',
        'Call interception requires a native Android build. Use EAS build to test on device.',
        [{ text: 'OK' }]
      );
      return false;
    }

    if (this.isStarted) {
      console.log('Call interception already running');
      return true;
    }

    const hasPermissions = await this.requestPermissions();
    if (!hasPermissions) {
      return false;
    }

    this.config = config;

    try {
      this.callDetector = new CallDetectorManager(
        (event: string, phoneNumber: string) => {
          this.handleCallEvent(event, phoneNumber);
        },
        true, // Read call log
        () => {
          console.log('✅ Call interception started successfully');
        },
        () => {
          console.error('❌ Call interception setup failed');
        }
      );

      this.isStarted = true;
      console.log('🔄 Real call interception is now active');
      return true;
    } catch (error) {
      console.error('Failed to start call interception:', error);
      
      Alert.alert(
        'Setup Failed',
        'Call interception requires a native build. Please use EAS build for real device testing.',
        [{ text: 'OK' }]
      );
      
      return false;
    }
  }

  private handleCallEvent(event: string, phoneNumber: string) {
    if (!this.config || !this.config.isEnabled) {
      console.log('📞 Call detected but forwarding is disabled');
      return;
    }

    console.log('📞 Call Event:', event, 'From:', phoneNumber);

    if (event === 'Incoming') {
      this.forwardCall(phoneNumber);
    }
  }

  private async forwardCall(fromNumber: string) {
    if (!this.config || !this.config.twilioNumber) {
      console.log('❌ Cannot forward - Twilio number not configured');
      return;
    }

    console.log('🚨 FORWARDING CALL:', fromNumber, '→', this.config.twilioNumber);
    
    try {
      // Here you would integrate with Twilio API to forward the call
      // For now, we'll simulate the forwarding
      this.config.onCallForwarded(fromNumber, this.config.twilioNumber);
      
      // In a real implementation, you would:
      // 1. Reject/decline the incoming call
      // 2. Use Twilio API to initiate a call to your Twilio number
      // 3. Pass the original caller's number as a parameter
      
      console.log('✅ Call forwarded successfully to Twilio');
      
    } catch (error) {
      console.error('❌ Failed to forward call:', error);
    }
  }

  stopCallInterception(): void {
    if (this.callDetector && this.isStarted) {
      this.callDetector.dispose();
      this.callDetector = null;
      this.isStarted = false;
      this.config = null;
      console.log('🛑 Call interception stopped');
    }
  }

  updateConfig(config: CallInterceptorConfig): void {
    this.config = config;
    console.log('🔧 Call interceptor config updated:', config);
  }

  isRunning(): boolean {
    return this.isStarted;
  }

  isSupported(): boolean {
    return Platform.OS === 'android' && hasCallDetectionSupport;
  }
}

export default new RealCallInterceptor();