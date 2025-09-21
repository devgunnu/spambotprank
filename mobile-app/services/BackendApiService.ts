import axios, { AxiosInstance, AxiosResponse } from 'axios';

export interface CallRouteRequest {
  callerId: string;
  timestamp: string;
  deviceId: string;
  action: 'route' | 'reject' | 'forward';
}

export interface CallRouteResponse {
  success: boolean;
  action: 'allow' | 'reject' | 'redirect';
  redirectNumber?: string;
  message?: string;
}

export interface BackendConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
}

class BackendApiService {
  private api: AxiosInstance;
  private config: BackendConfig;

  constructor(config: BackendConfig) {
    this.config = {
      timeout: 5000,
      ...config
    };

    this.api = axios.create({
      baseURL: this.config.baseUrl,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
      }
    });

    // Request interceptor for logging
    this.api.interceptors.request.use(
      (config) => {
        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for logging
    this.api.interceptors.response.use(
      (response) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('❌ API Response Error:', error.response?.status, error.message);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Route an incoming call through the backend server
   */
  async routeCall(request: CallRouteRequest): Promise<CallRouteResponse> {
    try {
      const response: AxiosResponse<CallRouteResponse> = await this.api.post('/route-call', request);
      return response.data;
    } catch (error) {
      console.error('Failed to route call:', error);
      // Fallback response in case of backend failure
      return {
        success: false,
        action: 'allow', // Default to allowing the call if backend fails
        message: 'Backend service unavailable'
      };
    }
  }

  /**
   * Notify backend about call status changes
   */
  async notifyCallStatus(callerId: string, status: 'answered' | 'rejected' | 'missed'): Promise<boolean> {
    try {
      await this.api.post('/call-status', {
        callerId,
        status,
        timestamp: new Date().toISOString()
      });
      return true;
    } catch (error) {
      console.error('Failed to notify call status:', error);
      return false;
    }
  }

  /**
   * Register device for call routing
   */
  async registerDevice(deviceId: string, phoneNumber?: string): Promise<boolean> {
    try {
      await this.api.post('/register-device', {
        deviceId,
        phoneNumber,
        platform: 'mobile',
        timestamp: new Date().toISOString()
      });
      return true;
    } catch (error) {
      console.error('Failed to register device:', error);
      return false;
    }
  }

  /**
   * Get call routing configuration from backend
   */
  async getRoutingConfig(): Promise<any> {
    try {
      const response = await this.api.get('/routing-config');
      return response.data;
    } catch (error) {
      console.error('Failed to get routing config:', error);
      return null;
    }
  }

  /**
   * Test backend connectivity
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.api.get('/health');
      return response.status === 200;
    } catch (error) {
      console.error('Backend connection test failed:', error);
      return false;
    }
  }

  /**
   * Update backend configuration
   */
  updateConfig(newConfig: Partial<BackendConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    // Update axios instance
    this.api.defaults.baseURL = this.config.baseUrl;
    this.api.defaults.timeout = this.config.timeout;
    
    if (this.config.apiKey) {
      this.api.defaults.headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }
  }
}

// Default configuration - you should update this with your actual backend URL
const defaultConfig: BackendConfig = {
  baseUrl: 'http://localhost:8000', // Update this with your Python FastAPI server URL
  timeout: 5000
};

export default new BackendApiService(defaultConfig);