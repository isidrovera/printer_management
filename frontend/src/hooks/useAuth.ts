import { create } from 'zustand';
import { LoginCredentials, User } from '../types/auth';
import { authService } from '../services/authService';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  
  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authService.login(credentials);
      set({ 
        isAuthenticated: true,
        isLoading: false,
        error: null
      });
    } catch (error) {
      set({ 
        isAuthenticated: false,
        isLoading: false,
        error: 'Credenciales inválidas'
      });
    }
  },
  
  logout: () => {
    authService.logout();
    set({ 
      user: null,
      isAuthenticated: false,
      error: null
    });
  }
}));