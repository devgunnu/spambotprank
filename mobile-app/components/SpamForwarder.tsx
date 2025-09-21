import React, { useEffect, useState } from 'react';
import {
    Alert,
    FlatList,
    ScrollView,
    StyleSheet,
    Switch,
    Text,
    TextInput,
    TouchableOpacity,
    View
} from 'react-native';
import RealCallInterceptor from '../services/RealCallInterceptor';

interface ForwardedCall {
  id: string;
  fromNumber: string;
  timestamp: Date;
  status: 'forwarded' | 'processing';
}

export default function SpamForwarder() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [twilioNumber, setTwilioNumber] = useState('');
  const [forwardedCalls, setForwardedCalls] = useState<ForwardedCall[]>([]);
  const [isInterceptionActive, setIsInterceptionActive] = useState(false);

  useEffect(() => {
    // Update the call interceptor when settings change
    const updateInterceptor = async () => {
      if (isEnabled && twilioNumber) {
        const success = await RealCallInterceptor.startCallInterception({
          isEnabled,
          twilioNumber,
          onCallForwarded: handleCallForwarded
        });
        setIsInterceptionActive(success);
      } else {
        RealCallInterceptor.stopCallInterception();
        setIsInterceptionActive(false);
      }
    };
    
    updateInterceptor();
  }, [isEnabled, twilioNumber]);

  const handleCallForwarded = (fromNumber: string, toNumber: string) => {
    const forwardedCall: ForwardedCall = {
      id: Date.now().toString(),
      fromNumber,
      timestamp: new Date(),
      status: 'forwarded'
    };
    
    setForwardedCalls(prev => [forwardedCall, ...prev.slice(0, 9)]);
    console.log('📞 Real call forwarded:', fromNumber, '→', toNumber);
  };

  const toggleSpamForwarding = async () => {
    const newState = !isEnabled;
    setIsEnabled(newState);
    
    if (newState) {
      console.log('🚨 Real call forwarding ENABLED - Intercepting incoming calls');
      if (!twilioNumber) {
        Alert.alert(
          'Twilio Number Required',
          'Please enter your Twilio number before enabling call forwarding.',
          [{ text: 'OK' }]
        );
        setIsEnabled(false);
        return;
      }
    } else {
      console.log('🛑 Call forwarding DISABLED');
    }
  };

  const saveConfiguration = () => {
    // Save to local storage or your backend
    console.log('Configuration saved:', { isEnabled, twilioNumber });
  };

  // Mock function to simulate receiving a call (replace with Twilio webhook)
  const simulateIncomingCall = () => {
    if (!isEnabled) {
      console.log('Spam forwarding is disabled - call not forwarded');
      return;
    }
    
    const mockCall: ForwardedCall = {
      id: Date.now().toString(),
      fromNumber: `+1${Math.floor(Math.random() * 9000000000) + 1000000000}`,
      timestamp: new Date(),
      status: 'forwarded'
    };
    
    setForwardedCalls(prev => [mockCall, ...prev.slice(0, 9)]); // Keep last 10 calls
    console.log('🚨 SPAM CALL FORWARDED:', mockCall.fromNumber, '→', twilioNumber);
  };

  const clearCallHistory = () => {
    setForwardedCalls([]);
  };

  const renderForwardedCall = ({ item }: { item: ForwardedCall }) => (
    <View style={styles.callItem}>
      <View style={styles.callHeader}>
        <Text style={styles.spamLabel}>🚨 SPAM</Text>
        <Text style={styles.timestamp}>
          {item.timestamp.toLocaleTimeString()}
        </Text>
      </View>
      <Text style={styles.phoneNumber}>{item.fromNumber}</Text>
      <Text style={styles.status}>Forwarded to → {twilioNumber || 'Not configured'}</Text>
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Spam Call Forwarder</Text>
      
      {/* Info Section */}
      <View style={styles.infoSection}>
        <Text style={styles.infoTitle}>📞 How It Works</Text>
        <Text style={styles.infoText}>
          1. Toggle spam forwarding ON{'\n'}
          2. Configure your Twilio number{'\n'}
          3. All incoming calls will be labeled as SPAM and forwarded{'\n'}
          4. Your algorithm will process them later
        </Text>
      </View>
      
      {/* Control Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Controls</Text>
        
        <View style={styles.toggleRow}>
          <Text style={styles.toggleLabel}>Forward All Calls as SPAM</Text>
          <Switch
            value={isEnabled}
            onValueChange={toggleSpamForwarding}
            trackColor={{ false: '#767577', true: '#ff4444' }}
            thumbColor={isEnabled ? '#ffffff' : '#f4f3f4'}
          />
        </View>

        <View style={styles.statusRow}>
          <Text style={styles.statusLabel}>Status:</Text>
          <Text style={[styles.statusValue, { color: isEnabled ? '#ff4444' : '#666' }]}>
            {isEnabled ? 'FORWARDING SPAM' : 'DISABLED'}
          </Text>
        </View>

        {/* Real-time Status Indicator */}
        <View style={[styles.statusContainer, isInterceptionActive ? styles.statusActive : styles.statusInactive]}>
          <Text style={styles.statusText}>
            Call Interception: {isInterceptionActive ? '🟢 Active' : '🔴 Inactive'}
          </Text>
          {isInterceptionActive && (
            <Text style={styles.statusSubtext}>
              Ready to intercept incoming calls
            </Text>
          )}
        </View>
      </View>

      {/* Configuration Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Configuration</Text>
        
        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Twilio Number</Text>
          <TextInput
            style={styles.textInput}
            value={twilioNumber}
            onChangeText={setTwilioNumber}
            placeholder="+1234567890"
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        <TouchableOpacity style={styles.saveButton} onPress={saveConfiguration}>
          <Text style={styles.buttonText}>Save Configuration</Text>
        </TouchableOpacity>
      </View>

      {/* Test Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Testing</Text>
        
        <TouchableOpacity 
          style={[styles.testButton, !isEnabled && styles.disabledButton]} 
          onPress={simulateIncomingCall}
          disabled={!isEnabled}
        >
          <Text style={styles.buttonText}>
            {isEnabled ? 'Simulate Incoming Call' : 'Enable Forwarding First'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Call History */}
      <View style={styles.section}>
        <View style={styles.historyHeader}>
          <Text style={styles.sectionTitle}>Forwarded Calls ({forwardedCalls.length})</Text>
          {forwardedCalls.length > 0 && (
            <TouchableOpacity style={styles.clearButton} onPress={clearCallHistory}>
              <Text style={styles.clearButtonText}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>
        
        {forwardedCalls.length === 0 ? (
          <Text style={styles.noCallsText}>No calls forwarded yet</Text>
        ) : (
          <FlatList
            data={forwardedCalls}
            renderItem={renderForwardedCall}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
            style={styles.callsList}
          />
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    color: '#333',
  },
  infoSection: {
    backgroundColor: '#e3f2fd',
    borderWidth: 1,
    borderColor: '#2196f3',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1976d2',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#1976d2',
    lineHeight: 20,
  },
  section: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  toggleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  toggleLabel: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  statusValue: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  inputContainer: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    color: '#333',
    marginBottom: 4,
    fontWeight: '500',
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 4,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  saveButton: {
    backgroundColor: '#2196f3',
    borderRadius: 4,
    padding: 12,
    alignItems: 'center',
  },
  testButton: {
    backgroundColor: '#ff4444',
    borderRadius: 4,
    padding: 12,
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  clearButton: {
    backgroundColor: '#ff9800',
    borderRadius: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  clearButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  noCallsText: {
    textAlign: 'center',
    color: '#666',
    fontStyle: 'italic',
    padding: 20,
  },
  callsList: {
    maxHeight: 300,
  },
  callItem: {
    backgroundColor: '#fff3f3',
    borderWidth: 1,
    borderColor: '#ffcdd2',
    borderRadius: 4,
    padding: 12,
    marginBottom: 8,
  },
  callHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  spamLabel: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#ff4444',
    backgroundColor: '#ffebee',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
  },
  timestamp: {
    fontSize: 12,
    color: '#666',
  },
  phoneNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  status: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  statusContainer: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
    borderWidth: 1,
  },
  statusActive: {
    backgroundColor: '#e8f5e8',
    borderColor: '#4caf50',
  },
  statusInactive: {
    backgroundColor: '#ffeaea',
    borderColor: '#f44336',
  },
  statusText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  statusSubtext: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
});