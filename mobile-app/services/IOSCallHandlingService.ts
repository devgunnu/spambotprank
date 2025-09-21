import { Alert } from 'react-native';

// Disabled iOS service - focusing on Android only
class IOSCallHandlingService {
  
  // All iOS functionality disabled
  async setupiOSNativeBlocking(): Promise<void> {
    Alert.alert('iOS Not Supported', 'This app is currently focused on Android functionality only.');
  }

  async addSpamNumbers(): Promise<void> {
    Alert.alert('iOS Not Supported', 'This app is currently focused on Android functionality only.');
  }
}

export default new IOSCallHandlingService();