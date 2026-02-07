import { create } from 'zustand';
import { api } from '../lib/api';

interface User {
  id: number;
  email: string;
  username: string;
  roles: string[];
  is_verified: boolean;
  // Add other fields as needed from UserDetail
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  
  login: (credentials: FormData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  loading: false,

  login: async (formData) => {
    set({ loading: true });
    try {
      // 1. Get Access Token
      const res = await api.post('/auth/login', formData, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        // Skip interceptor for this request to avoid loop if 401? No, login is public.
      });
      
      const { access_token } = res.data;
      set({ accessToken: access_token, isAuthenticated: true });

      // 2. Fetch User Profile
      await get().checkAuth();
      
    } finally {
      set({ loading: false });
    }
  },

  logout: async () => {
    try {
        await api.post('/auth/logout');
    } catch (e) {
        // Ignore errors on logout
    }
    set({ user: null, accessToken: null, isAuthenticated: false });
  },

  refreshToken: async () => {
      // Calls endpoint which uses HTTP-only cookie
      const res = await api.post('/auth/refresh');
      const { access_token } = res.data;
      set({ accessToken: access_token, isAuthenticated: true });
  },

  checkAuth: async () => {
      // Validate current token or fetch user if we have token
      // If we don't have user but have token:
      try {
        const res = await api.get('/users/me');
        set({ user: res.data, isAuthenticated: true });
      } catch (e) {
          // If 401, the interceptor will try to refresh.
          // If that fails, it will call logout.
          // So we don't need to do much here.
      }
  }
}));
