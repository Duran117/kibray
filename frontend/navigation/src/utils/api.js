/**
 * API utility for Kibray navigation system
 * Handles all API calls to Django backend with JWT authentication
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
const TOKEN_KEY = 'kibray_access_token';
const REFRESH_KEY = 'kibray_refresh_token';

// Token management functions
export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const getRefreshToken = () => localStorage.getItem(REFRESH_KEY);
export const setRefreshToken = (token) => localStorage.setItem(REFRESH_KEY, token);
export const removeTokens = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
};
export const isAuthenticated = () => Boolean(getToken());

// Token refresh logic
const refreshAccessToken = async () => {
  try {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token');
    }
    
    const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    
    if (!response.ok) {
      throw new Error('Refresh failed');
    }
    
    const data = await response.json();
    setToken(data.access);
    return data.access;
  } catch (error) {
    console.error('Token refresh error:', error);
    removeTokens();
    // Don't auto-redirect - let React Router handle it
    // window.location.href = '/login';
    throw error;
  }
};

// Fetch with automatic authentication and token refresh
const fetchWithAuth = async (url, options = {}) => {
  const token = getToken();
  const headers = {
    ...options.headers,
  };
  
  // Only add Content-Type: application/json if body is NOT FormData
  // FormData sets its own Content-Type with boundary automatically
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  let response = await fetch(url, { ...options, headers });
  
  // Handle 401 Unauthorized - try to refresh token
  if (response.status === 401) {
    try {
      const newToken = await refreshAccessToken();
      headers['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(url, { ...options, headers });
    } catch (err) {
      throw new Error('Authentication failed');
    }
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }
  
  return response.json();
};

// API interface
export const api = {
  // Authentication
  login: async (username, password) => {
    const response = await fetch(`${API_BASE}/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    
    if (!response.ok) {
      throw new Error('Invalid credentials');
    }
    
    const data = await response.json();
    setToken(data.access);
    setRefreshToken(data.refresh);
    return data;
  },
  
  logout: () => {
    removeTokens();
    // Use React Router navigation instead
    // window.location.href = '/login';
  },
  
  // CRUD operations
  get: async (endpoint) => {
    return fetchWithAuth(`${API_BASE}${endpoint}`);
  },
  
  post: async (endpoint, data) => {
    // Handle FormData differently from JSON
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return fetchWithAuth(`${API_BASE}${endpoint}`, {
      method: 'POST',
      body,
    });
  },
  
  put: async (endpoint, data) => {
    return fetchWithAuth(`${API_BASE}${endpoint}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  
  patch: async (endpoint, data) => {
    return fetchWithAuth(`${API_BASE}${endpoint}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
  
  delete: async (endpoint) => {
    return fetchWithAuth(`${API_BASE}${endpoint}`, {
      method: 'DELETE',
    });
  },
};

export const MOCK_MODE = false;
export default api;
