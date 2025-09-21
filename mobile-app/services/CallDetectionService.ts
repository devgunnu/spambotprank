import { Alert, PermissionsAndroid, Platform } from 'react-native';

// Platform-specific import
let CallDetectorManager: any = null;
let hasCallDetectionSupport = false;

if (Platform.OS === 'android') {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const callDetection = require('react-native-call-detection');
    CallDetectorManager = callDetection.default || callDetection;
    hasCallDetectionSupport = true;
  } catch (error) {
    console.warn('Call detection not available on this platform:', error);
    hasCallDetectionSupport = false;
  }
}

export interface CallEvent {
  callerId: string;
  timestamp: Date;
  status: 'incoming' | 'answered' | 'disconnected';
}

export interface CallDetectionOptions {
  onIncomingCall: (event: CallEvent) => void;
  onCallAnswered: (event: CallEvent) => void;
  onCallDisconnected: (event: CallEvent) => void;
}

class CallDetectionService {
  private callDetector: any = null;
  private isStarted: boolean = false;
  private options: CallDetectionOptions | null = null;

  async requestPermissions(): Promise<boolean> {
    if (Platform.OS === 'web') {
      console.warn('Permissions not applicable on web platform');
      return true;
    }

    if (Platform.OS === 'android') {
      try {
        const permissions = [
          PermissionsAndroid.PERMISSIONS.READ_PHONE_STATE,
          PermissionsAndroid.PERMISSIONS.CALL_PHONE,
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        ];

        const results = await PermissionsAndroid.requestMultiple(permissions);
        
        return Object.values(results).every(
          result => result === PermissionsAndroid.RESULTS.GRANTED
        );
      } catch (error) {
        console.error('Permission request failed:', error);
        return false;
      }
    }
    
    // For iOS, permissions are handled through Info.plist
    return true;
  }

  async startCallDetection(options: CallDetectionOptions): Promise<boolean> {
    if (Platform.OS !== 'android') {
      console.warn('Call detection is only supported on Android platform');
      Alert.alert(
        'Platform Not Supported',
        'Call detection is only available on Android devices with native builds.',
        [{ text: 'OK' }]
      );
      return false;
    }

    if (!hasCallDetectionSupport || !CallDetectorManager) {
      console.error('Call detection library not available');
      Alert.alert(
        'Call Detection Unavailable',
        'Call detection requires a native Android build and is not supported in Expo Go. Please build a development build or EAS build to test call routing functionality.',
        [{ text: 'OK' }]
      );
      return false;
    }

    if (this.isStarted) {
      console.warn('Call detection is already started');
      return true;
    }

    const hasPermissions = await this.requestPermissions();
    if (!hasPermissions) {
      Alert.alert(
        'Permissions Required',
        'Please grant phone and audio permissions to use call routing features.'
      );
      return false;
    }

    this.options = options;

    try {
      this.callDetector = new CallDetectorManager((event: any, phoneNumber: string) => {
        console.log('Call detection event:', event, phoneNumber);
        
        const callEvent: CallEvent = {
          callerId: phoneNumber || 'Unknown',
          timestamp: new Date(),
          status: this.mapCallState(event)
        };

        switch (event) {
          case 'Incoming':
            options.onIncomingCall(callEvent);
            break;
          case 'Offhook': // Call answered
            options.onCallAnswered(callEvent);
            break;
          case 'Disconnected':
            options.onCallDisconnected(callEvent);
            break;
          default:
            console.log('Unknown call state:', event);
        }
      }, true, () => {
        console.log('Call detection setup completed');
      }, () => {
        console.error('Call detection setup failed');
      });

      this.isStarted = true;
      console.log('Call detection service started successfully');
      return true;
    } catch (error) {
      console.error('Failed to start call detection:', error);
      
      // Check if it's the BatchedBridge error specifically
      if (error instanceof TypeError && error.message.includes('BatchedBridge')) {
        console.warn('Call detection requires a native Android build - not available in Expo Go');
        Alert.alert(
          'Call Detection Unavailable',
          'Call detection requires a native Android build and is not supported in Expo Go. Please build a development build or EAS build to test call routing functionality.',
          [{ text: 'OK' }]
        );
      }
      
      return false;
    }
  }

  stopCallDetection(): void {
    if (this.callDetector && this.isStarted) {
      this.callDetector.dispose();
      this.callDetector = null;
      this.isStarted = false;
      this.options = null;
      console.log('Call detection service stopped');
    }
  }

  isRunning(): boolean {
    return this.isStarted;
  }

  isSupported(): boolean {
    return Platform.OS === 'android' && hasCallDetectionSupport;
  }

  private mapCallState(state: string): 'incoming' | 'answered' | 'disconnected' {
    switch (state) {
      case 'Incoming':
        return 'incoming';
      case 'Offhook':
        return 'answered';
      case 'Disconnected':
        return 'disconnected';
      default:
        return 'disconnected';
    }
  }
}

export default new CallDetectionService();