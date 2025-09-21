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
  private isStarted: boolean = false;

  async requestPermissions(): Promise<boolean> {
    // No permissions needed for Twilio approach
    console.log('Using Twilio approach - no device permissions required');
    return true;
  }

  async startCallDetection(options: CallDetectionOptions): Promise<boolean> {
    console.log('Using Twilio approach - call detection not needed on device');
    this.isStarted = true;
    return true;
  }

  stopCallDetection(): void {
    this.isStarted = false;
    console.log('Twilio call routing stopped');
  }

  isRunning(): boolean {
    return this.isStarted;
  }

  isSupported(): boolean {
    // Always supported since we're using Twilio
    return true;
  }
}

export default new CallDetectionService();