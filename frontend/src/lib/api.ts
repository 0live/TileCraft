import axios from 'axios';
import { useAuthStore } from '../store/auth';

export const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Inject Access Token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401 & Refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Trigger refresh only on 401 and if it hasn't been retried yet
    // AND ensuring we don't get into an infinite loop if auth endpoints themselves return 401
    const isAuthEndpoint = originalRequest.url?.includes('/auth/');
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      try {
        // Attempt to refresh the token using the HTTP-only cookie
        await useAuthStore.getState().refreshToken();

        // Update the header with the new token (optional if request interceptor picks it up, 
        // but safe to set explicitly here if axios doesn't re-run request interceptors on retry inside the same instance usually? 
        // Actually, retrying via `api(originalRequest)` WILL run request interceptors again.
        // So we just need to make sure the store is updated (which refreshToken does).
        
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed (or was invalid), so logout
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
