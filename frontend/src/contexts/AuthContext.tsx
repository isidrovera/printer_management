// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../lib/axios';
import { User, TokenResponse, LoginCredentials, LoginResponse } from '../types/auth';

interface AuthContextType {
  user: User | null;
  token: TokenResponse | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<TokenResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedToken = localStorage.getItem('token');
        if (!storedToken) {
          setIsLoading(false);
          return;
        }

        const tokenData: TokenResponse = JSON.parse(storedToken);
        if (!tokenData || !tokenData.access_token) {
          throw new Error('Token inválido');
        }

        setToken(tokenData);
        axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
        
        const response = await axiosInstance.get<User>('/auth/me');
        setUser(response.data);
      } catch (error) {
        console.error('Error en la inicialización de auth:', error);
        await logout();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      console.log('🔄 Iniciando login:', credentials.username);
      const response = await axiosInstance.post('/auth/login', credentials);
      const { access_token, token_type, user: userData } = response.data;
      
      const tokenData: TokenResponse = {
        access_token,
        token_type
      };

      localStorage.setItem('token', JSON.stringify(tokenData));
      
      setToken(tokenData);
      setUser(userData);
      
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      if (userData.must_change_password) {
        navigate('/change-password');
      } else {
        navigate('/dashboard');
      }
    } catch (error: any) {
      console.error('Error en login:', error);
      throw new Error(
        error.response?.data?.message || 
        'Error al iniciar sesión. Por favor, verifica tus credenciales.'
      );
    }
  };

  const logout = async () => {
    try {
      if (token?.access_token) {
        await axiosInstance.post('/auth/logout');
      }
    } catch (error) {
      console.error('Error en logout:', error);
    } finally {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
      delete axiosInstance.defaults.headers.common['Authorization'];
      navigate('/login');
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      login,
      logout,
      isAuthenticated: !!token?.access_token,
      isLoading
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
};