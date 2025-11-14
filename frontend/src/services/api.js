/**
 * API Service Layer - Axios wrapper for backend communication
 * Base URL: http://localhost:8000/api
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add JWT token to all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      console.warn('401 Unauthorized - Token may be expired or invalid');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Only redirect if not already on login page
      if (window.location.pathname !== '/login') {
        console.log('Redirecting to login page...');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ============= AUTH API =============

export const authAPI = {
  login: async (phone, fullName = '', email = '') => {
    const response = await apiClient.post('/auth/login', {
      phone,
      full_name: fullName,
      email,
    });
    // Save token and user to localStorage
    localStorage.setItem('token', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
    return response.data;
  },

  me: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getCurrentUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },
};

// ============= CASES API =============

export const casesAPI = {
  create: async (caseData) => {
    const response = await apiClient.post('/cases', caseData);
    return response.data;
  },

  getAll: async () => {
    const response = await apiClient.get('/cases');
    return response.data;
  },

  getById: async (caseId) => {
    const response = await apiClient.get(`/cases/${caseId}`);
    return response.data;
  },

  update: async (caseId, updates) => {
    const response = await apiClient.patch(`/cases/${caseId}`, updates);
    return response.data;
  },

  delete: async (caseId) => {
    const response = await apiClient.delete(`/cases/${caseId}`);
    return response.data;
  },

  finalize: async (caseId) => {
    const response = await apiClient.post(`/cases/${caseId}/finalize`);
    return response.data;
  },
};

// ============= DOCUMENTS API =============

export const documentsAPI = {
  upload: async (caseId, file, title, side) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('side', side);

    const response = await apiClient.post(
      `/cases/${caseId}/documents`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  getAll: async (caseId) => {
    const response = await apiClient.get(`/cases/${caseId}/documents`);
    return response.data;
  },

  getById: async (caseId, documentId, includeText = false) => {
    const response = await apiClient.get(
      `/cases/${caseId}/documents/${documentId}`,
      {
        params: { include_text: includeText },
      }
    );
    return response.data;
  },

  delete: async (caseId, documentId) => {
    const response = await apiClient.delete(
      `/cases/${caseId}/documents/${documentId}`
    );
    return response.data;
  },
};

// ============= VERDICTS API =============

export const verdictsAPI = {
  generateInitial: async (caseId) => {
    const response = await apiClient.post(`/cases/${caseId}/verdict`);
    return response.data;
  },

  getAll: async (caseId) => {
    const response = await apiClient.get(`/cases/${caseId}/verdicts`);
    return response.data;
  },

  getByRound: async (caseId, round) => {
    const response = await apiClient.get(`/cases/${caseId}/verdicts/${round}`);
    return response.data;
  },
};

// ============= ARGUMENTS API =============

export const argumentsAPI = {
  submit: async (caseId, side, argumentText) => {
    const response = await apiClient.post(`/cases/${caseId}/arguments`, {
      side,
      argument_text: argumentText,
    });
    return response.data;
  },

  getAll: async (caseId) => {
    const response = await apiClient.get(`/cases/${caseId}/arguments`);
    return response.data;
  },
};

export default apiClient;
