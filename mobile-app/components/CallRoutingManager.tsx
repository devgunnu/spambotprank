import React, { useEffect, useState } from 'react';
import {
    Alert,
    ScrollView,
    StyleSheet,
    Switch,
    Text,
    TextInput,
    TouchableOpacity,
    View
} from 'react-native';
import CallRoutingService, { CallRoutingConfig, CallRoutingStats } from '../services/CallRoutingService';
import CallDetectionService from '../services/CallDetectionService';

export default function CallRoutingManager() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000');
  const [apiKey, setApiKey] = useState('');
  const [stats, setStats] = useState<CallRoutingStats>({
    totalCalls: 0,
    routedCalls: 0,
    rejectedCalls: 0,
  });
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isPlatformSupported, setIsPlatformSupported] = useState(true);

  useEffect(() => {
    loadConfiguration();
    updateStats();
    
    // Set up periodic stats updates
    const interval = setInterval(updateStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadConfiguration = async () => {
    try {
      const config = CallRoutingService.getConfiguration();
      setIsEnabled(config.enabled);
      setBackendUrl(config.backendUrl);
      setApiKey(config.apiKey || '');
      setIsRunning(CallRoutingService.isRunning());
    } catch (err) {
      console.error('Failed to load configuration:', err);
    }
  };

  const updateStats = () => {
    const currentStats = CallRoutingService.getStats();
    setStats(currentStats);
    setIsRunning(CallRoutingService.isRunning());
  };

  const testConnection = async () => {
    setIsLoading(true);
    try {
      const connected = await CallRoutingService.testBackendConnection();
      setIsConnected(connected);
      
      Alert.alert(
        'Connection Test',
        connected ? 'Successfully connected to backend!' : 'Failed to connect to backend.',
        [{ text: 'OK' }]
      );
    } catch (error) {
      setIsConnected(false);
      Alert.alert('Connection Error', 'Failed to test connection.', [{ text: 'OK' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfiguration = async () => {
    setIsLoading(true);
    try {
      const config: Partial<CallRoutingConfig> = {
        enabled: isEnabled,
        backendUrl,
        apiKey: apiKey || undefined,
      };

      CallRoutingService.updateConfiguration(config);
      
      // Initialize with new configuration
      const success = await CallRoutingService.initialize(config);
      
      if (success) {
        Alert.alert('Success', 'Configuration saved successfully!', [{ text: 'OK' }]);
      } else {
        Alert.alert('Error', 'Failed to save configuration.', [{ text: 'OK' }]);
      }
    } catch (error) {
      console.error('Failed to save configuration:', error);
      Alert.alert('Error', 'Failed to save configuration.', [{ text: 'OK' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCallRouting = async () => {
    setIsLoading(true);
    try {
      if (isRunning) {
        CallRoutingService.stopCallRouting();
        setIsRunning(false);
      } else {
        // Ensure service is initialized with current config
        await CallRoutingService.initialize({
          enabled: isEnabled,
          backendUrl,
          apiKey: apiKey || undefined,
        });
        
        const success = await CallRoutingService.startCallRouting();
        if (success) {
          setIsRunning(true);
        } else {
          Alert.alert('Error', 'Failed to start call routing. Please check permissions and configuration.', [{ text: 'OK' }]);
        }
      }
    } catch (error) {
      console.error('Failed to toggle call routing:', error);
      Alert.alert('Error', 'Failed to toggle call routing.', [{ text: 'OK' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetStats = () => {
    Alert.alert(
      'Reset Statistics',
      'Are you sure you want to reset all call statistics?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: () => {
            CallRoutingService.resetStats();
            updateStats();
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Call Routing Manager</Text>
      
      {/* Status Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Status</Text>
        <View style={styles.statusRow}>
          <Text style={styles.statusLabel}>Service Status:</Text>
          <Text style={[styles.statusValue, { color: isRunning ? '#4CAF50' : '#f44336' }]}>
            {isRunning ? 'Running' : 'Stopped'}
          </Text>
        </View>
        <View style={styles.statusRow}>
          <Text style={styles.statusLabel}>Backend:</Text>
          <Text style={[styles.statusValue, { color: isConnected ? '#4CAF50' : '#f44336' }]}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Text>
        </View>
      </View>

      {/* Configuration Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Configuration</Text>
        
        <View style={styles.configRow}>
          <Text style={styles.configLabel}>Enable Call Routing</Text>
          <Switch
            value={isEnabled}
            onValueChange={setIsEnabled}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor={isEnabled ? '#f5dd4b' : '#f4f3f4'}
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Backend URL</Text>
          <TextInput
            style={styles.textInput}
            value={backendUrl}
            onChangeText={setBackendUrl}
            placeholder="http://localhost:8000"
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>API Key (Optional)</Text>
          <TextInput
            style={styles.textInput}
            value={apiKey}
            onChangeText={setApiKey}
            placeholder="Enter API key"
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.button, styles.testButton]}
            onPress={testConnection}
            disabled={isLoading}
          >
            <Text style={styles.buttonText}>Test Connection</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.saveButton]}
            onPress={saveConfiguration}
            disabled={isLoading}
          >
            <Text style={styles.buttonText}>Save Config</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Control Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Control</Text>
        
        <TouchableOpacity
          style={[styles.button, styles.mainButton, { backgroundColor: isRunning ? '#f44336' : '#4CAF50' }]}
          onPress={toggleCallRouting}
          disabled={isLoading || !isEnabled}
        >
          <Text style={styles.buttonText}>
            {isRunning ? 'Stop Call Routing' : 'Start Call Routing'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Statistics Section */}
      <View style={styles.section}>
        <View style={styles.statsHeader}>
          <Text style={styles.sectionTitle}>Statistics</Text>
          <TouchableOpacity style={styles.resetButton} onPress={resetStats}>
            <Text style={styles.resetButtonText}>Reset</Text>
          </TouchableOpacity>
        </View>
        
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{stats.totalCalls}</Text>
            <Text style={styles.statLabel}>Total Calls</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{stats.routedCalls}</Text>
            <Text style={styles.statLabel}>Routed</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{stats.rejectedCalls}</Text>
            <Text style={styles.statLabel}>Rejected</Text>
          </View>
        </View>

        {stats.lastCall && (
          <View style={styles.lastCallContainer}>
            <Text style={styles.lastCallTitle}>Last Call</Text>
            <Text style={styles.lastCallText}>From: {stats.lastCall.callerId}</Text>
            <Text style={styles.lastCallText}>Time: {stats.lastCall.timestamp.toLocaleString()}</Text>
            <Text style={styles.lastCallText}>Action: {stats.lastCall.action}</Text>
          </View>
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
    marginBottom: 12,
    color: '#333',
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusLabel: {
    fontSize: 16,
    color: '#666',
  },
  statusValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  configRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  configLabel: {
    fontSize: 16,
    color: '#333',
  },
  inputContainer: {
    marginBottom: 12,
  },
  inputLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 4,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  button: {
    flex: 1,
    padding: 12,
    borderRadius: 4,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  testButton: {
    backgroundColor: '#2196F3',
  },
  saveButton: {
    backgroundColor: '#FF9800',
  },
  mainButton: {
    marginHorizontal: 0,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  statsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  resetButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#f44336',
    borderRadius: 4,
  },
  resetButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  lastCallContainer: {
    backgroundColor: '#f9f9f9',
    padding: 12,
    borderRadius: 4,
    borderLeftWidth: 4,
    borderLeftColor: '#2196F3',
  },
  lastCallTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  lastCallText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
});