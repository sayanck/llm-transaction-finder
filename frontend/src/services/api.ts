// API service for communicating with the backend

import axios from 'axios';
import { ApiResponse, SummaryStats, PatternData, AnalysisResult, SuspiciousThread } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 seconds timeout for LLM analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create a separate instance for analysis with longer timeout
const analysisApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 3 minutes timeout for analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    if (error.response?.status === 500) {
      throw new Error('Server error occurred. Please try again later.');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout. The analysis is taking longer than expected.');
    } else if (!error.response) {
      throw new Error('Network error. Please check your connection and ensure the backend is running.');
    }
    throw error;
  }
);

// Add interceptors for analysis API
analysisApi.interceptors.request.use(
  (config) => {
    console.log(`Making analysis request to ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Analysis request error:', error);
    return Promise.reject(error);
  }
);

analysisApi.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Analysis response error:', error);
    if (error.response?.status === 500) {
      throw new Error('Analysis server error. Please try again later.');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Analysis timeout. The AI is processing a large dataset. Please wait or try again.');
    } else if (!error.response) {
      throw new Error('Network error during analysis. Please check your connection.');
    }
    throw error;
  }
);

export const apiService = {
  // Health check
  async healthCheck(): Promise<{ status: string; gemini_configured: boolean }> {
    const response = await api.get('/health');
    return response.data;
  },

  // Get transaction summary statistics
  async getSummary(): Promise<ApiResponse<SummaryStats>> {
    const response = await api.get('/api/summary');
    return response.data;
  },

  // Get identified patterns
  async getPatterns(): Promise<ApiResponse<PatternData>> {
    const response = await api.get('/api/patterns');
    return response.data;
  },

  // Trigger LLM analysis (optimized)
  async analyzePatterns(): Promise<ApiResponse<AnalysisResult>> {
    const response = await analysisApi.post('/api/analyze');
    return response.data;
  },

  // Trigger progressive LLM analysis
  async analyzePatternsProgressive(): Promise<ApiResponse<AnalysisResult>> {
    const response = await analysisApi.post('/api/analyze-progressive');
    return response.data;
  },

  // Get all suspicious threads
  async getThreads(): Promise<ApiResponse<{
    threads: SuspiciousThread[];
    total_count: number;
    risk_distribution: {
      high: number;
      medium: number;
      low: number;
    };
  }>> {
    const response = await api.get('/api/threads');
    return response.data;
  },

  // Upload a data file (CSV or Excel)
  async uploadFile(file: File): Promise<ApiResponse<{ file_path: string }>> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Get current active file info
  async getCurrentFile(): Promise<ApiResponse<{ file_path: string | null; using_default: boolean }>> {
    const response = await api.get('/api/current-file');
    return response.data;
  },
};

export default apiService;
